
# Secure-Communication-and-Video-Streaming


A Python-based project that implements secure client-server communication and video streaming using RSA encryption. The server manages client connections, handles public key distribution, and ensures secure message exchange and video streaming without local storage.


## Commands to run

first start server in one terminal: 

- python .\Server.py

run code for client:

- python .\Client.py

Client will ask for name, after that you can enter:

- just enter string if you want to broadcast message to every client
- encrypt : if you want to send encrypted message to particular client. This will prompt you to enter receiver name and message to send
- video : if you want to play video , available on server, this will prompt you with available videos on server
- quit : if you want to quit - end this connection


    

## Functions used in client.py

- receive_video_frames(sock) : his function receives video frames from the server over the socket and displays them using OpenCV. It continuously receives frame size information, then receives frame data until the entire frame is received.

- receive_messages(sock) : This function receives messages from the server over the socket. It handles various types of messages, including updating the client dictionary, decrypting encrypted messages, displaying regular messages and displaying the list of available videos.

- send_message(sock) : This function allows the user to send messages to the server over the socket sock. It supports sending regular messages, requesting to play a video, and encrypting and sending messages.


## Functions used in server.py

- handle_client(client_socket) : This function manages communication with a client, receiving messages, and responding appropriately. It updates the clients_dict dictionary with client names and keys, broadcasts messages to all clients, handles video-related requests, and removes clients from the dictionary when they disconnect.

- broadcast(message) : This function broadcasts a message to all clients in the clients list. It serializes the message to JSON format and sends it to each client, ensuring that all clients receive the broadcasted message.

- send_vid(client_socket, video_name) : This function handles the transmission of video frames to a client. It prepares paths for different resolutions of the requested video, reads and resizes frames, and sends them over the socket to the client. Once all frames are sent, it sends a special frame to indicate the end of video transmission.
