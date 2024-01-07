import os
import cv2
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import pyttsx3
import pytesseract
import moviepy.editor as mp

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Function to extract text from images using Tesseract OCR
def extract_text_from_images(folder_path, progress_var):
    image_files = [f for f in os.listdir(folder_path) if f.endswith(('png', 'jpg', 'jpeg'))]

    extracted_text = ""
    total_images = len(image_files)
    for i, image_file in enumerate(image_files, start=1):
        image_path = os.path.join(folder_path, image_file)
        img = cv2.imread(image_path)
        text = pytesseract.image_to_string(img)
        extracted_text += text + "\n"

        # Update progress bar
        progress = int((i / total_images) * 100)
        progress_var.set(progress)
        root.update_idletasks()

    return extracted_text

# Function to generate voice-over
def generate_voice_over(text, output_path, progress_var):
    engine = pyttsx3.init()
    engine.save_to_file(text, os.path.join(output_path, 'voice_over.mp3'))
    engine.runAndWait()

    # Save transcript to a text file
    with open(os.path.join(output_path, 'transcript.txt'), 'w') as file:
        file.write(text)

    # Update progress bar to 100% after completion
    progress_var.set(100)
    root.update_idletasks()

# Function to add text overlay synchronized with the voice-over
def add_text_overlay(video_clip, transcript_text, output_folder):
    text_clips = []
    current_time = 0
    duration_per_word = 0.8  # Adjust duration per word display as needed

    # Splitting the text into words and generating timestamps
    for word in transcript_text.split():
        # Define styling elements for text
        text_styling = {
            'fontsize': 30,
            'color': 'white',
            'bg_color': 'black',
            'size': video_clip.size,  # Match text size to video size
            'method': 'label'
        }
        text_clip = mp.TextClip(word, **text_styling).set_start(current_time).set_duration(duration_per_word)
        text_clips.append(text_clip)
        current_time += duration_per_word

    # Combine text clips using CompositeVideoClip
    text_overlay = mp.CompositeVideoClip(text_clips).set_duration(video_clip.duration)

    # Overlay text on the video clip
    final_clip = mp.CompositeVideoClip([video_clip, text_overlay.set_position(('center', 720))])

    return final_clip

# Function to handle folder selection and execute the process
def process_folder():
    folder_selected = filedialog.askdirectory(title="Select Folder Containing Images")
    if folder_selected:
        progress_var = tk.IntVar()
        progress_bar = ttk.Progressbar(root, variable=progress_var, length=200, mode='determinate')
        progress_bar.pack(pady=10)

        text = extract_text_from_images(folder_selected, progress_var)
        output_folder = filedialog.askdirectory(title="Select Output Folder")

        if output_folder:
            generate_voice_over(text, output_folder, progress_var)
            print("Transcript and voice-over generated successfully!")

            # Ask user to select the background video
            background_video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi")])
            if background_video_path:
                final_output_path = os.path.join(output_folder, "output_video.mp4")
                video_clip = mp.VideoFileClip(background_video_path)
                audio_clip = mp.AudioFileClip(os.path.join(output_folder, "voice_over.mp3"))

                if video_clip.duration > audio_clip.duration:
                    video_clip = video_clip.subclip(0, audio_clip.duration)

                video_clip = video_clip.set_audio(audio_clip.set_duration(video_clip.duration))

                # Your code to calculate cropping area and set TikTok format...
                landscape_width = video_clip.size[0]
                landscape_height = video_clip.size[1]

                # Calculate cropping area to maintain center and fit in 9:16 aspect ratio
                target_width = landscape_height * 9 // 16  # Maintain the aspect ratio
                crop_width = min(landscape_width, target_width)
                crop_height = landscape_height

                x1 = (landscape_width - crop_width) // 2
                y1 = 0
                x2 = x1 + crop_width
                y2 = crop_height    

                # Crop the video accordingly and set to TikTok format
                final_clip = video_clip.crop(x1=x1, y1=y1, x2=x2, y2=y2).resize((1080, 1920)).set_duration(video_clip.duration)

                # Add text overlay synchronized with the voice-over
                transcript_text = open(os.path.join(output_folder, 'transcript.txt')).read()
                final_clip = add_text_overlay(final_clip, transcript_text, output_folder)

                final_clip.write_videofile(final_output_path, codec="libx264", audio_codec="aac", fps=24)

                print("Background video with synchronized voice-over and text overlay generated successfully!")

                # Close the GUI window
                root.destroy()

# GUI setup and main loop
root = tk.Tk()
root.title("Image to Transcript Converter with Voice-over and Text Overlay")
root.geometry("300x300")

label = tk.Label(root, text="Select a folder containing images:")
label.pack(pady=10)

button = tk.Button(root, text="Select Folder", command=process_folder)
button.pack(pady=10)

root.mainloop()
