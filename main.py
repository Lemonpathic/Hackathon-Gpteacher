import os
import io
import openai
from boto.s3.connection import S3Connection
import re
from flask import Flask, render_template, request
from collections import namedtuple
from PIL import Image, ImageDraw, ImageFont
from google.cloud import vision

UPLOAD_FOLDER = 'uploaded'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

openai.api_key = os.environ['OPENAI_KEY']
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'serviceaccounttoken.json'


@app.route('/')
def init():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def index():
    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '':
            try:
                enum_images = list(enumerate(os.listdir(app.config['UPLOAD_FOLDER'])))
                greatest = max(enum_images)
                greatest_iteration = greatest[0]
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], 'image' + str(greatest_iteration)))
            except:
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], 'image' + '0'))

    image_file_path = ('uploaded/' + "image" + str(greatest_iteration))
    print(image_file_path)

    client = vision.ImageAnnotatorClient()
    print(image_file_path)

    def prepare_image_local(image_path):
        try:
            # Loads the image into memory
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            return image
        except Exception as e:
            print(e)
            return

    image = prepare_image_local(image_file_path)

    class VisionAI:
        Text_Detection = namedtuple('Text_Detection', ('description', 'bounding_poly'))

        def __init__(self, client, image):
            self.client = client
            self.image = image

        def text_detection(self):
            response = self.client.text_detection(image=self.image)
            texts = response.text_annotations
            if texts:
                results = []
                for text in texts:
                    results.append(self.Text_Detection(text.description, text.bounding_poly.vertices))
                return results
            return

    def generate_flash_cards(notes):
        prompt = f"Create flash cards from these notes {notes}, make sure for each you do Front: Back:"

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
        return flash_cards

    va = VisionAI(client, image)
    text = va.text_detection()
    text_content = text[0].description

    gpt_response = generate_flash_cards(text_content)

    va = VisionAI(client, image)
    text = va.text_detection()
    text_content = text[0].description

    # print(text[0].description)

    def split_cards(text_cards):
        separate_cards = text_cards.split('\n\n')
        cards = []  # Initialize a list to store dictionaries for each card

        for card in separate_cards:
            # Initialize a dictionary for the card
            text = card
            front_pattern = r"Front:\s(.*?)\n"  # This regex captures the text after "Front: "
            back_pattern = r"Back:(.*?)$"

            # Use re.search() to find the pattern for "Front"
            front_match = re.search(front_pattern, text)
            if front_match:

                cards.append(front_match.group(1))  # Store the "Front" text in the dictionary
            else:
                cards.append("Front pattern not found in the text.")
            # Use re.search() to find the pattern for "Back"

            back_match = re.search(back_pattern, text)
            if back_match:
                cards.append(back_match.group(1))  # Store the "Back" text in the dictionary
            else:
                cards.append("Back pattern not found in the text.")

        return cards

    cards = split_cards(gpt_response)  # Call the function to split the cards

    def front_split(cards):
        fronts = []
        for index, card in enumerate(cards):
            if index == 0 or (index % 2 == 0):
                fronts.append(card)
        return fronts

    def back_split(cards):
        back = []
        for index, card in enumerate(cards):
            if index % 2 != 0:
                back.append(card.lstrip())
        return back

    fronts = front_split(cards)
    backs = back_split(cards)

    def create_dict(front, back):
        cards_dict = []
        for index, card in enumerate(fronts):
            card_template = {
                "front": front[index],
                "back": back[index]
            }
            cards_dict.append(card_template)
        return cards_dict

    flash_dic = create_dict(fronts, backs)

    return render_template("index.html", data=flash_dic)


if __name__ == '__main__':
    app.run(debug=True)
