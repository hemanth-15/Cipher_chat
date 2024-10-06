import socket
import threading
import json
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
import numpy as np
import base64
import struct
import pickle
import cv2
import os
VIDEO_DIRECTORY = "videos"
# Dictionary to store names and keys received from the server
client_dict = {}
available_videos = []


def receive_video_frames(sock):
    
    while True:
        # Receive frame size
        frame_size_data = sock.recv(8)
        if not frame_size_data:
            break
        frame_size = struct.unpack("Q", frame_size_data)[0]

        frame_data = b""
        while len(frame_data) < frame_size:
            data = sock.recv(frame_size - len(frame_data))
            if not data:
                break
            frame_data += data

        if (frame_data == b'done'):
            break

        # Deserialize frame data
        frame = pickle.loads(frame_data)
        # Display the frame
        cv2.imshow("Received Video", frame)
        
        
        if cv2.waitKey(33) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()


def receive_messages(sock):
    global client_dict, available_videos
    while True:
        try:
            # Receive message from server
            data = sock.recv(1024)
            if not data:
                break

            message = data.decode()

            if message == "video_start":
                receive_video_frames(sock)
                

            # Deserialize the received message
            try:
                message = json.loads(data.decode())
            except json.JSONDecodeError:
                # If the message is not a valid JSON, continue to the next iteration
                continue

            # Check message type using flags
            if message.get("type") == "dictionary":
                # Update client dictionary
                client_dict = message["data"]
                # Print the updated dictionary
                print("Updated dictionary:------------------------------------")
                for name, key in client_dict.items():
                    print(f"{name}")
            elif message.get("type") == "mess_en":
                # Decrypt the encrypted message
                encrypted_message_base64 = message["data"]
                #print(f"Received encrypted message: {encrypted_message_base64}")
                encrypted_message = base64.b64decode(encrypted_message_base64.encode())
                #print(f"Decoded encrypted message: {encrypted_message}")
                try:
                    cipher = PKCS1_OAEP.new(RSA.import_key(private_key.encode()))
                    decrypted_message = cipher.decrypt(encrypted_message).decode()
                    print(f"Decrypted message from server: {decrypted_message}")
                except Exception as e:
                    #print("this message is not for you")
                    pass
            elif message.get("type") == "message":
                # Print the received message
                print(f"Message from server: {message['data']}")
            elif message.get("type") == "video_end":
                print("Video streaming ended. Closing video window.")
                cv2.destroyAllWindows()
            elif message.get("type") == "video_list":
                # Update available videos
                available_videos = message["data"]
                # Print available videos
                print("Available videos:")
                for i, video in enumerate(available_videos, start=1):
                    print(f"{i}. {video}")


            elif message.get("type") == "quit":
                # Close the socket
                sock.close()
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

    sock.close()




def send_message(sock):
    global available_videos
    while True:
        try:
            # Send message to server
            message = input("Enter message to send (video | quit | encrypt | (if message, just enter message to send)): ")
            if message.lower() == "quit":
                quit_message = {"type": "quit", "name": name}
                message_str = json.dumps(quit_message)
                sock.send(message_str.encode())
                break
            elif message.lower() == "encrypt":
                # Print all client names
                print("Choose a client to send an encrypted message:")
                for client_name in client_dict.keys():
                    print(client_name)
                receiver_name = input("Enter receiver's name: ")
                if receiver_name in client_dict:
                    receiver_public_key = client_dict[receiver_name]
                    #print(f"receivier public key: {receiver_public_key}")
                    # Get message to encrypt
                    message_to_encrypt = input("Enter message to encrypt: ")
                    # Encrypt message using receiver's public key
                    cipher = PKCS1_OAEP.new(RSA.import_key(receiver_public_key))
                    encrypted_message = cipher.encrypt(message_to_encrypt.encode())
                    encrypted_message_base64 = base64.b64encode(encrypted_message).decode()
                    message_data = {"type": "mess_en", "data": encrypted_message_base64}
                    message_str = json.dumps(message_data)
                    sock.send(message_str.encode())
                else:
                    print("Receiver not found in dictionary.")
                        # Serialize message
            elif message.lower() == "video":
                print("Choose which video to play(enter vid_(number))")
                vid_message = {"type": "video"}
                message_str = json.dumps(vid_message)
                sock.sendall(message_str.encode())
            elif message.lower().startswith("vid_"):  # Check if the input is a number
                # Assume the input is the index of the video to play
                chosen_video = message
                message_data = {"type": "video_request", "data": chosen_video}
                message_str = json.dumps(message_data)
                sock.sendall(message_str.encode())
            else:
                message_data = {"type": "message", "data": f"{name}: {message}"}
                message_str = json.dumps(message_data)
                sock.send(message_str.encode())
        except Exception as e:
            print(f"Error sending message: {e}")
            break

    sock.close()



# keys generation
rsa = RSA.generate(1024)
public_key = rsa.publickey().export_key().decode()
private_key = rsa.export_key().decode()

# Create a TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the server
client_socket.connect(("localhost", 5050))

# Send name and key to server
name = input("Enter your name: ")
#key = input("Enter your key: ")
message_data = {"type": "name_key", "name": name, "key": public_key}
message_str = json.dumps(message_data)
#printing private key for demo
#print(private_key)
client_socket.send(message_str.encode())

# Start thread for receiving messages
receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
receive_thread.start()

# Start thread for sending messages
send_thread = threading.Thread(target=send_message, args=(client_socket,))
send_thread.start()

# Wait for threads to finish
receive_thread.join()
send_thread.join()

print("Client closed.")
