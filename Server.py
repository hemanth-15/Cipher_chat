import socket
import threading
import json
import struct
import pickle
import imutils
import cv2
import os

VIDEO_DIRECTORY = "videos"
# Dictionary to store clients names and keys
clients_dict = {}

video_files = os.listdir(VIDEO_DIRECTORY)
available_videos = [video_file for video_file in video_files if video_file.endswith(".mp4")]

def send_vid(client_socket,  video_name):
    resol=["360","720","1080"]
    
    video_paths = [os.path.join(VIDEO_DIRECTORY, f"{video_name}_{res}.mp4") for res in resol]

    caps=[cv2.VideoCapture(path) for path in video_paths]

    total_frames=int(caps[0].get(cv2.CAP_PROP_FRAME_COUNT))
    frame_size= total_frames // 3

    i = 1
    while i < len(caps):
        start_frame = frame_size * i
        caps[i].set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        i += 1


    for ca in caps:
        for _ in range(frame_size):
            ret, frame= ca.read()
            if not ret:
                break
            frame=imutils.resize(frame, width=1080)
            frame_data=pickle.dumps(frame)
            frame_size = len(frame_data)
            #message=struct.pack("Q",len(frame_data)) + frame_data
            #client_socket.sendall(message)
            client_socket.sendall(struct.pack("Q", frame_size))
            # Send frame data
            client_socket.sendall(frame_data)
    
    client_socket.sendall(struct.pack("Q", len(b'done')) + b'done')
    print("video sending completed...")
    

    for ca in caps:
        ca.release()


def handle_client(client_socket):
    global clients_dict
    while True:
        try:
            # Receive message from client
            data = client_socket.recv(1024)
            if not data:
                break

            # Deserialize the received message
            message = json.loads(data.decode())

            # Check message type using flags
            if message.get("type") == "name_key":
                # Add name and key to dictionary
                clients_dict[message["name"]] = message["key"]
                print(f"Added {message['name']} to the dictionary.")

                # Broadcast updated dictionary to all clients
                broadcast({"type": "dictionary", "data": clients_dict})
            elif message.get("type") == "message":
                # Broadcast the message to all clients
                broadcast(message)
            elif message.get("type") == "mess_en":
                # Broadcast the encrypted message
                print("broadcasting encrypted text")
                broadcast(message)

            elif message.get("type") == "video":
                print("Requested video list...")
                # Send list of available videos to client
                client_socket.sendall(json.dumps({"type": "video_list", "data": available_videos}).encode())

            elif message.get("type") == "video_request":
                video_name = message.get("data")
                
                # Assuming videos are in a folder named "videos"
                try:
                    client_socket.sendall("video_start".encode())
                    send_vid(client_socket, video_name)
                except Exception as e:
                    print(f"Error sending video: {e}")
                   
            
            elif message.get("type") == "quit":
                # Remove client's name and key from dictionary
                name = message.get("name")
                if name in clients_dict:
                    del clients_dict[name]
                    print(f"Removed {name} from the dictionary.")
                else:
                    print(f"Error: {name} not found in dictionary.")

                # Broadcast updated dictionary to all clients
                broadcast({"type": "dictionary", "data": clients_dict})

                # Inform all clients that the client left the chat
                broadcast({"type": "message", "data": f"{name} left the chat."})
                break
        except Exception as e:
            print(f"Error handling client: {e}")
            break

    client_socket.close()


def broadcast(message):
    # Send message to all clients
    for client_socket in clients:
        try:
            message_str = json.dumps(message)
            client_socket.send(message_str.encode())
        except Exception as e:
            print(f"Error broadcasting message: {e}")


# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the address and port
server_socket.bind(("localhost", 5050))

# Listen for incoming connections
server_socket.listen(5)

# List to store client sockets
clients = []

print("Server started.")

try:
    while True:
        # Accept a new connection
        client_socket, address = server_socket.accept()
        print(f"Accepted connection from {address}")

        # Add the client socket to the list
        clients.append(client_socket)

        # Create a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()
except KeyboardInterrupt:
    print("Server shutting down.")
finally:
    # Close all client sockets
    print("Ctrl + C pressed: Server shutting down.")
    for client_socket in clients:
        client_socket.close()

    # Close the server socket
    server_socket.close()
