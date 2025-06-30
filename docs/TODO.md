# TODO

- [ ] Version checking - store compatible firmware version and warn user if their controller is out of date (with link to updater script)
   - Also warn if python is probably out of date (because firmware is too new)

- [ ] Refactor the `packet.py` structure.
   - There is a lot of bloat using dictionaries to pass information when we could just be using the new protobuf structure.
   - We still have code left over from previous library that predated protobuf
   - Look at firmware implementation for a cleaner approach
- [ ] Configuration commands are fire-and-forget (no response validation)
   - We have a response system for command ACK if needed
