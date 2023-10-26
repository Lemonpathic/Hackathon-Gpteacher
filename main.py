import os
import io
import openai
from boto.s3.connection import S3Connection
import re
from flask import Flask, render_template, request
from collections import namedtuple
from PIL import Image, ImageDraw, ImageFont
from google.cloud import vision
from werkzeug.utils import secure_filename
import docx2txt

UPLOAD_FOLDER = 'uploaded'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

openai.api_key = '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'
# openai.api_key = os.environ['OPENAI_KEY']
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'serviceaccounttoken.json'


@app.route('/')
def init():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def index():
    # extracted_text = []
    # uploaded_files = []
    # for file_upload in request.files.getlist('file'):
    #     uploaded_files.append(file_upload)
    # for uploaded_file in uploaded_files:
    #
    #     if uploaded_file.filename != '':
    #         # Use the secure_filename function to ensure the filename is safe
    #         filename = secure_filename(uploaded_file.filename)
    #         file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    #         uploaded_file.save(file_path)
    #
    #         # Determine the file type based on the extension
    #         file_extension = filename.rsplit('.', 1)[1].lower()
    #
    #         if file_extension in ('jpg', 'jpeg', 'png'):
    #
    #             image_file_path = file_path
    #             client = vision.ImageAnnotatorClient()
    #
    #             def prepare_image_local(image_path):
    #                 try:
    #                     # Loads the image into memory
    #                     with io.open(image_path, 'rb') as image_file:
    #                         content = image_file.read()
    #                     image = vision.Image(content=content)
    #                     return image
    #                 except Exception as e:
    #                     print(e)
    #                     return
    #
    #             image = prepare_image_local(image_file_path)
    #
    #             class VisionAI:
    #                 Text_Detection = namedtuple('Text_Detection', ('description', 'bounding_poly'))
    #
    #                 def __init__(self, client, image):
    #                     self.client = client
    #                     self.image = image
    #
    #                 def text_detection(self):
    #                     response = self.client.text_detection(image=self.image)
    #                     texts = response.text_annotations
    #                     if texts:
    #                         results = []
    #                         for text in texts:
    #                             results.append(self.Text_Detection(text.description, text.bounding_poly.vertices))
    #                         return results
    #                     return
    #
    #             va = VisionAI(client, image)
    #             text = va.text_detection()
    #             text_content = text[0].description
    #             extracted_text.append(text_content)
    #             text_content = ' '.join(extracted_text)
    #         elif file_extension in ('pdf', 'doc', 'docx', 'txt'):
    #             text_content = docx2txt.process(uploaded_file)
    #

    def generate_flash_cards(notes):
        prompt = f"Create flash cards from the notes provided. Each flashcard should be structured with ‘Front:’ and ‘Back:’." \
                 f" Please ensure that the answers are in simple line form, not in bullet points or dashes. Keep the explanations simple and concise," \
                 f"  for easy memorization." \
                 f" Remember, these are flashcards and they are meant to aid in memorization. Here are the notes:"

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": notes}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.03,
            max_tokens=800

        )

        flash_cards = response['choices'][0]['message']['content']
        # print(flash_cards)
        return flash_cards

    # gpt_response = generate_flash_cards(text_content)

    def split_cards(text_cards):
        separate_cards = text_cards.split('\n')
        filtered_separate_cards = []
        for card in separate_cards:
            if card != ' ':
                filtered_separate_cards.append(card)
        # print(filtered_separate_cards)

        cards = []  # Initialize a list to store dictionaries for each card

        for card_face, card in enumerate(filtered_separate_cards):
            card_data = {}  # Initialize a dictionary for the card
            front = False

            if card_face % 2 == 0:
                front = True
            if front:
                card_data['Front'] = card.replace('Front: ', '')
                print(card_data['Front'])

            # else:
            #     card_data['Front'] = "Front pattern not found in the text."

            if not front:
                card_data['Back'] = card.replace('Back: ', '')
            # else:
            #     card_data['Back'] = "Back pattern not found in the text."

            cards.append(card_data)  # Append the dictionary to the list
        return cards

    gpt_response_ex = r"""Front: How did trade develop in Mesopotamia?
Back: Villagers traded surplus grain for building materials and started organizing specific jobs.
Front: What is the title of the chapter in the history book?
Back: Ancient Mesopotamia
Front: What are the big idea questions for this chapter?
Back: How did farming develop due to the river? What are other ways that the river helped people? Did villages tend to be near the river, and why?
Front: What are the two rivers that flow through Mesopotamia?
Back: Tigris and Euphrates
Front: What is the climate of Mesopotamia?
Back: Semi-arid with hot summers and little rain
Front: How did farmers deal with unpredictable floods?
Back: They built irrigation canals to water crops
Front: What resources did Mesopotamia lack?
Back: Wood and metal
Front: What were houses and walls in villages made of?
Back: Mud
Front: What did villagers trade their surplus grain for?
Back: Building materials
Front: What is the strategy to turn dreams into reality?
Back: Acting on purpose
Front: What are the four quadrants of importance and urgency?
Back: 1) Important and urgent, 2) Important and not urgent, 3) Not important and urgent, 4) Not important or urgent
Front: What are activities in Quadrant I?
Back: Important and urgent activities done under the pressure of looming deadlines
Front: What are activities in Quadrant II?
Back: Important activities done without the pressure of looming deadlines

"""
    # print(gpt_response_ex)
    cards = split_cards(gpt_response_ex)

    data_list = {}
    for i in range(0, len(cards), 2):
        front_key = cards[i]
        back_value = cards[i + 1]
        data_list[front_key] = back_value


    return render_template("index.html", data=cards)


if __name__ == '__main__':
    app.run(debug=True)
