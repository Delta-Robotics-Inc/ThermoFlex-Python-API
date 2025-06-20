# Thermoflex Status System Improvements

## Current System Analysis

### Existing Implementation
The current status system in the Thermoflex Python API uses a simple request-response model:
- Basic status requests via `status(type)` method
- Two status types: 'compact' and 'dump'
- Blocking status requests with sleep delays
- Limited status validation and error handling
- No streaming or subscription capabilities

### Protocol Buffer Integration
The system currently uses protocol buffers (`tfnode_messages_pb2.py`) for message definitions but doesn't fully leverage their capabilities:

```protobuf
message GetStatusCommand {
    Device device = 1;
    DeviceStatusMode mode = 2;
    bool repeating = 4;
}

message StatusResponse {
    Device device = 1;
    oneof status_response {
        NodeStatusCompact node_status_compact = 2;
        NodeStatusDump node_status_dump = 3;
        SMAStatusCompact sma_status_compact = 4;
        SMAStatusDump sma_status_dump = 5;
    }
}
```

## Proposed Improvements

### 1. Protocol Buffer Integration

#### Message Structure
The protocol buffer definitions provide a solid foundation but should be enhanced:

```protobuf
// Add to tfnode-messages.proto
message StatusSubscription {
    Device device = 1;
    DeviceStatusMode mode = 2;
    float interval = 3;  // Update interval in seconds
    bool continuous = 4; // Whether to stream continuously
}

message StatusStream {
    uint32 sequence_number = 1;
    uint64 timestamp = 2;
    StatusResponse status = 3;
    StatusMetadata metadata = 4;
}

message StatusMetadata {
    float latency = 1;
    uint32 missed_updates = 2;
    DeviceStatus device_status = 3;
}

enum DeviceStatus {
    DEVICE_STATUS_UNKNOWN = 0;
    DEVICE_STATUS_ACTIVE = 1;
    DEVICE_STATUS_INACTIVE = 2;
    DEVICE_STATUS_ERROR = 3;
}
```

### 2. ROS-like Communication Patterns

#### Topics and Messages
Implement a topic-based system similar to ROS:

```python
class StatusTopic:
    """Represents a status data stream"""
    def __init__(self, name: str, msg_type: type):
        self.name = name
        self.msg_type = msg_type
        self.publishers = []
        self.subscribers = []

class StatusPublisher:
    """Publishes status updates to a topic"""
    def __init__(self, topic: StatusTopic):
        self.topic = topic
        self.sequence = 0

    async def publish(self, status_data: StatusResponse):
        # Create StatusStream message
        stream_msg = StatusStream(
            sequence_number=self.sequence,
            timestamp=int(time.time() * 1e9),
            status=status_data,
            metadata=StatusMetadata(...)
        )
        self.sequence += 1
        # Notify subscribers
        for subscriber in self.topic.subscribers:
            await subscriber.callback(stream_msg)

class StatusSubscriber:
    """Subscribes to status updates from a topic"""
    def __init__(self, topic: StatusTopic, callback: Callable):
        self.topic = topic
        self.callback = callback
        self.topic.subscribers.append(self)
```

### 3. Asynchronous Status Management

#### Status Manager Implementation
```python
class StatusManager:
    """Manages status communication for a node"""
    def __init__(self, node: 'Node'):
        self.node = node
        self.topics = {
            'node_status': StatusTopic('node_status', NodeStatusCompact),
            'node_dump': StatusTopic('node_dump', NodeStatusDump),
            'sma_status': StatusTopic('sma_status', SMAStatusCompact),
            'sma_dump': StatusTopic('sma_dump', SMAStatusDump)
        }
        self.publishers = {
            name: StatusPublisher(topic)
            for name, topic in self.topics.items()
        }

    async def request_status(self, 
                           status_type: DeviceStatusMode,
                           device: Device = Device.DEVICE_NODE,
                           timeout: float = 5.0) -> StatusResponse:
        """Request status update with timeout"""
        cmd = GetStatusCommand(
            device=device,
            mode=status_type,
            repeating=False
        )
        return await self._send_command(cmd, timeout)

    async def start_status_stream(self,
                                status_type: DeviceStatusMode,
                                device: Device = Device.DEVICE_NODE,
                                interval: float = 1.0):
        """Start continuous status updates"""
        cmd = GetStatusCommand(
            device=device,
            mode=status_type,
            repeating=True
        )
        # Start background task for status streaming
        asyncio.create_task(self._stream_status(cmd, interval))
```

### 4. Status Validation and Error Handling

#### Schema Validation
```python
from pydantic import BaseModel, Field

class NodeStatusValidator(BaseModel):
    """Validates node status data"""
    uptime: int = Field(ge=0)
    error_code: int = Field(ge=0)
    v_supply: float = Field(ge=0)
    pot_val: float = Field(ge=0)
    
    class Config:
        extra = 'forbid'  # Reject unknown fields

class StatusValidator:
    """Validates all status types"""
    def __init__(self):
        self.validators = {
            DeviceStatusMode.STATUS_COMPACT: NodeStatusValidator,
            # Add other validators...
        }

    def validate(self, status_type: DeviceStatusMode, data: dict) -> bool:
        validator = self.validators.get(status_type)
        if not validator:
            return True  # No validator for this type
        try:
            validator(**data)
            return True
        except Exception as e:
            logger.error(f"Status validation failed: {e}")
            return False
```

## Implementation Considerations

### 1. Backward Compatibility
- Maintain existing status methods while adding new functionality
- Provide migration path for existing code
- Support both old and new status formats during transition

### 2. Performance
- Use protocol buffer serialization for efficient message transfer
- Implement message batching for high-frequency updates
- Consider using zero-copy operations where possible
- Implement proper buffer management to prevent memory issues

### 3. Reliability
- Implement proper error handling and recovery
- Add status validation at multiple levels
- Include sequence numbers for message tracking
- Add timeout and retry mechanisms

### 4. Monitoring and Debugging
- Add comprehensive logging
- Include status metadata (latency, missed updates)
- Provide status visualization tools
- Implement status history tracking

## Example Usage

### Basic Status Request
```python
# Get current status
status = await node.status_manager.request_status(
    status_type=DeviceStatusMode.STATUS_COMPACT
)

# Subscribe to status updates
async def status_callback(msg: StatusStream):
    print(f"Status update {msg.sequence_number}: {msg.status}")

subscriber = node.status_manager.subscribe(
    'node_status',
    status_callback
)

# Start status streaming
await node.status_manager.start_status_stream(
    status_type=DeviceStatusMode.STATUS_COMPACT,
    interval=0.5
)
```

### Advanced Usage
```python
# Create custom status topic
custom_topic = StatusTopic('custom_status', CustomStatusMessage)
publisher = StatusPublisher(custom_topic)

# Multiple subscribers with filters
async def filtered_callback(msg: StatusStream):
    if msg.status.device == Device.DEVICE_PORT1:
        process_port1_status(msg)

subscriber1 = custom_topic.subscribe(filtered_callback)

# Status validation
validator = StatusValidator()
if validator.validate(DeviceStatusMode.STATUS_COMPACT, status_data):
    publisher.publish(status_data)
```

## Future Improvements

1. **Message Queue Integration**
   - Add support for message queues (e.g., ZeroMQ, RabbitMQ)
   - Implement pub/sub patterns for distributed systems
   - Add message persistence for offline operation

2. **Status Aggregation**
   - Add support for aggregating status from multiple nodes
   - Implement status statistics and analysis
   - Add support for status-based triggers and actions

3. **Security**
   - Add message authentication
   - Implement status encryption
   - Add access control for status topics

4. **Monitoring and Visualization**
   - Add real-time status visualization
   - Implement status dashboards
   - Add status-based alerting

## Conclusion

The proposed improvements would bring several benefits:
1. More reliable and efficient status communication
2. Better integration with protocol buffers
3. ROS-like patterns for familiar communication models
4. Improved error handling and validation
5. Better support for streaming and real-time updates
6. More flexible and extensible status system

The implementation should be done in phases:
1. Protocol buffer integration
2. Basic status manager implementation
3. Topic-based communication
4. Advanced features (streaming, validation, etc.)
5. Monitoring and visualization tools 