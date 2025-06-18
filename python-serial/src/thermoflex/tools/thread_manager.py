"""
Improved thread management system for Thermoflex library.

This module provides proper thread lifecycle management following Python best practices:
- Graceful shutdown with timeouts
- Thread state tracking
- Proper error handling
- Context manager support
- Logging integration
"""

import threading
import time
import weakref
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from .debug import Debugger as D, DEBUG_LEVELS

class ThreadState(Enum):
    """Thread lifecycle states"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class ManagedThread:
    """Enhanced thread wrapper with lifecycle management"""
    
    def __init__(self, target: Callable, args: tuple = (), kwargs: dict = None, 
                 name: str = None, daemon: bool = True, shutdown_timeout: float = 5.0):
        self.target = target
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.shutdown_timeout = shutdown_timeout
        self.state = ThreadState.INITIALIZING
        self.error = None
        self.stop_event = threading.Event()
        
        # Create thread with proper naming
        thread_name = name or f"{target.__name__}_{id(self)}"
        self.thread = threading.Thread(
            target=self._run_wrapper,
            name=thread_name,
            daemon=daemon
        )
        
        D.debug(DEBUG_LEVELS['DEBUG'], "ThreadManager", f"Created thread: {thread_name}")
    
    def _run_wrapper(self):
        """Thread execution wrapper with error handling"""
        try:
            self.state = ThreadState.RUNNING
            D.debug(DEBUG_LEVELS['INFO'], "ThreadManager", f"Thread {self.thread.name} started")
            
            # Pass stop_event to target function if it accepts it
            import inspect
            sig = inspect.signature(self.target)
            if 'stop_event' in sig.parameters:
                self.kwargs['stop_event'] = self.stop_event
            
            self.target(*self.args, **self.kwargs)
            
        except Exception as e:
            self.state = ThreadState.ERROR
            self.error = e
            D.debug(DEBUG_LEVELS['ERROR'], "ThreadManager", 
                   f"Thread {self.thread.name} error: {e}")
        finally:
            if self.state != ThreadState.ERROR:
                self.state = ThreadState.STOPPED
            D.debug(DEBUG_LEVELS['INFO'], "ThreadManager", 
                   f"Thread {self.thread.name} finished with state: {self.state.value}")
    
    def start(self):
        """Start the thread"""
        self.thread.start()
        return self
    
    def stop(self, timeout: Optional[float] = None):
        """Gracefully stop the thread"""
        if self.state not in [ThreadState.RUNNING, ThreadState.INITIALIZING]:
            return True
        
        timeout = timeout or self.shutdown_timeout
        D.debug(DEBUG_LEVELS['INFO'], "ThreadManager", 
               f"Stopping thread {self.thread.name} (timeout: {timeout}s)")
        
        self.state = ThreadState.STOPPING
        self.stop_event.set()
        
        self.thread.join(timeout=timeout)
        
        if self.thread.is_alive():
            D.debug(DEBUG_LEVELS['WARNING'], "ThreadManager", 
                   f"Thread {self.thread.name} did not stop gracefully within {timeout}s")
            return False
        
        return True
    
    def is_alive(self) -> bool:
        """Check if thread is alive"""
        return self.thread.is_alive()
    
    @property
    def name(self) -> str:
        """Get thread name"""
        return self.thread.name

class ThreadManager:
    """Central thread management system"""
    
    def __init__(self):
        self._threads: Dict[str, ManagedThread] = {}
        self._lock = threading.RLock()
        self._shutdown_in_progress = False
        
    def create_thread(self, target: Callable, args: tuple = (), kwargs: dict = None,
                     name: str = None, daemon: bool = True, 
                     shutdown_timeout: float = 5.0, start: bool = True) -> ManagedThread:
        """Create and optionally start a managed thread"""
        
        with self._lock:
            if self._shutdown_in_progress:
                raise RuntimeError("Cannot create threads during shutdown")
            
            thread = ManagedThread(
                target=target, args=args, kwargs=kwargs,
                name=name, daemon=daemon, shutdown_timeout=shutdown_timeout
            )
            
            if start:
                thread.start()
            
            self._threads[thread.name] = thread
            D.debug(DEBUG_LEVELS['DEBUG'], "ThreadManager", 
                   f"Registered thread: {thread.name}")
            
            return thread
    
    def get_thread(self, name: str) -> Optional[ManagedThread]:
        """Get thread by name"""
        with self._lock:
            return self._threads.get(name)
    
    def list_threads(self) -> List[ManagedThread]:
        """List all managed threads"""
        with self._lock:
            return list(self._threads.values())
    
    def cleanup_stopped_threads(self):
        """Remove stopped threads from tracking"""
        with self._lock:
            stopped_threads = [
                name for name, thread in self._threads.items()
                if not thread.is_alive() and thread.state in [ThreadState.STOPPED, ThreadState.ERROR]
            ]
            
            for name in stopped_threads:
                thread = self._threads.pop(name)
                D.debug(DEBUG_LEVELS['DEBUG'], "ThreadManager", 
                       f"Cleaned up stopped thread: {name}")
    
    def shutdown_all(self, timeout: float = 10.0, force_after: float = 2.0) -> bool:
        """
        Shutdown all threads gracefully
        
        Args:
            timeout: Total time to wait for all threads
            force_after: Time to wait for each individual thread
        
        Returns:
            True if all threads stopped gracefully, False otherwise
        """
        with self._lock:
            if self._shutdown_in_progress:
                D.debug(DEBUG_LEVELS['WARNING'], "ThreadManager", "Shutdown already in progress")
                return True
            
            self._shutdown_in_progress = True
            
        D.debug(DEBUG_LEVELS['INFO'], "ThreadManager", 
               f"Shutting down {len(self._threads)} threads...")
        
        start_time = time.time()
        all_stopped = True
        
        # Get snapshot of threads to avoid modification during iteration
        threads_to_stop = list(self._threads.values())
        
        # Step 1: Signal all threads to stop
        for thread in threads_to_stop:
            if thread.is_alive():
                thread.stop_event.set()
                thread.state = ThreadState.STOPPING
        
        # Step 2: Wait for threads to stop gracefully
        for thread in threads_to_stop:
            if not thread.is_alive():
                continue
                
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time <= 0:
                D.debug(DEBUG_LEVELS['WARNING'], "ThreadManager", 
                       f"Timeout reached, {thread.name} still running")
                all_stopped = False
                continue
            
            wait_time = min(force_after, remaining_time)
            success = thread.stop(timeout=wait_time)
            
            if not success:
                all_stopped = False
                D.debug(DEBUG_LEVELS['WARNING'], "ThreadManager", 
                       f"Thread {thread.name} did not stop gracefully")
        
        # Step 3: Report results
        alive_threads = [t for t in threads_to_stop if t.is_alive()]
        if alive_threads:
            thread_names = [t.name for t in alive_threads]
            D.debug(DEBUG_LEVELS['ERROR'], "ThreadManager", 
                   f"Failed to stop threads: {thread_names}")
        else:
            D.debug(DEBUG_LEVELS['INFO'], "ThreadManager", "All threads stopped successfully")
        
        with self._lock:
            self._threads.clear()
            self._shutdown_in_progress = False
        
        return all_stopped
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup"""
        self.shutdown_all()

# Global thread manager instance
thread_manager = ThreadManager()

# Legacy compatibility functions
def threaded(func: Callable) -> Callable:
    """
    Legacy threaded decorator - now uses ThreadManager
    
    DEPRECATED: Use thread_manager.create_thread() directly for new code
    """
    def wrapper(*args, **kwargs):
        name = f"{func.__name__}_{int(time.time())}"
        return thread_manager.create_thread(
            target=func, args=args, kwargs=kwargs, name=name
        )
    return wrapper

def get_all_threads() -> List[ManagedThread]:
    """Get all managed threads (legacy compatibility)"""
    return thread_manager.list_threads()

def stop_all_threads(timeout: float = 10.0) -> bool:
    """Stop all threads (legacy compatibility)"""
    return thread_manager.shutdown_all(timeout=timeout)

# Global stop event for backward compatibility
stop_threads_flag = threading.Event()

def set_global_stop_flag():
    """Set the global stop flag (legacy compatibility)"""
    stop_threads_flag.set()
    # Also signal all managed threads
    for thread in thread_manager.list_threads():
        thread.stop_event.set() 