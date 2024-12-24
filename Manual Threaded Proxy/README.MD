This is a manual threaded proxy that can help study and account for incoming and outgoing packets from a device. It handles http and https requests separately, the https can be decrypted for further information.
  For http requests, /1.1 is converted to /1.0 packet to avoid persistent connections and help optimize the performance. For https, the proxy handles it by making 2 threads that handle receiving and sending packets
from the packets to the server, acting as a transparent listener. 
