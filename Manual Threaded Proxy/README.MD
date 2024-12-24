This is a manual threaded proxy that can help study and account for incoming and outgoing packets from a device. It handles http and https requests separately, the https can be decrypted for further information.
  For http requests, /1.1 is converted to /1.0 packet to avoid persistent connections and help optimize the performance. For https, the proxy handles it by making 2 threads that handle receiving and sending packets
from the packets to the server, acting as a transparent listener. 

Usage:
   - python proxy.py <port>
   - While creating proxy on the browser the host should be localhost i.e. 127.0.0.1 and port number-the one that is given as input as shown in the previous point. (We had some issue with windows blocking the IP 0.0.0.0)
Example:
    python proxy.py 8080

Requirements:
- The script listens on the specified <port> for incoming HTTP/HTTPS requests.
- It forwards these requests to the intended destination, relaying the responses back to the client.
- Supports HTTP CONNECT tunneling for HTTPS traffic.

