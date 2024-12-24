This lab assignment demonstrates a custom UDP Application Protocol (UAP) using two different concurrency models for both the client and server:

Thread-based model: Each thread waits for a single event (e.g., network input or keyboard input).
Non-blocking I/O or asynchronous model: A single thread waits for multiple events using asynchronous I/O. This model can also be implemented using multi-threading depending on the language.

The goal of this assignment is to implement both client and server sides for both the threaded and non-threaded approaches, allowing all four combinations to work together.

Project Structure
This project implements a UDP-based client-server application in Python using two concurrency models: thread-based and non-threaded/asynchronous.

Folder A:
	Non-threaded Server (asyncio)
	Thread-based Client (threading)
Folder B:
	Thread-based Server (threading)
	Non-threaded Client (asyncio)

How to run:
Note: Make sure you have python3 in the location /usr/bin/python3 to run the files without any interpreter (./server.py instead of python3 server.py). Make sure you use "chmod +x <file_name>" to set the permissions to use it directly as ./server.py. You can use the normal interpreters to run the files normally (python3 ./server.py). 

1) You can go to any folder (A or B) and type the following commands to run. You can try any of the 4 combinations of client and server.
	if you have python3 and in the location /usr/bin/python3
		Server : 
			./server.py <port_num>
		Client: (use 127.0.0.1 instead of localhost)
			./client.py 127.0.0.1 <port_num>
			or
			./client.py 127.0.0.1 <port_num> <input_file>
	else:
		Server :
			python server.py <port_num>
		Client : (use 127.0.0.1 instead of localhost) 
			./client.py 127.0.0.1 <port_num>
			or
			./client.py 127.0.0.1 <port_num> <input_file>

2) To check the concurrency, you can run the 2 clients together along with the server of your choice.
