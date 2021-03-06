# Import flask and other such stuff
from flask import Flask, request, jsonify
import boto3
import io
from PIL import Image
import cv2
import numpy
from keys import AMAZON_KEYS_REC
from pprint import pprint

#Output text
output = ""

# Capture image
cap = cv2.VideoCapture(0)

# Setup up aws
rekognition = boto3.client('rekognition', region_name='us-east-1', aws_access_key_id=AMAZON_KEYS_REC[0], aws_secret_access_key=AMAZON_KEYS_REC[1])
dynamodb = boto3.client('dynamodb', region_name='us-east-1', aws_access_key_id=AMAZON_KEYS_REC[0], aws_secret_access_key=AMAZON_KEYS_REC[1])
s3 = boto3.resource('s3', aws_access_key_id=AMAZON_KEYS_REC[0], aws_secret_access_key=AMAZON_KEYS_REC[1])


import requests

app = Flask(__name__)

@app.route('/uploadImage', methods=['POST'])
def yeet():
    data = request.files['image']
    print(type(data))



    # Aws facial recognition
    image = Image.open(data)
    stream = io.BytesIO()
    image.save(stream, format="JPEG")
    image_binary = stream.getvalue()

    response = rekognition.detect_faces(
        Image={'Bytes': image_binary}
    )

    all_faces = response['FaceDetails']

    # Initialize list object
    boxes = []

    # Get image diameters

    image_width = image.size[0]
    image_height = image.size[1]

    # Crop face from image
    for face in all_faces:
        box = face['BoundingBox']
        x1 = int(box['Left'] * image_width) * 0.9
        y1 = int(box['Top'] * image_height) * 0.9
        x2 = int(box['Left'] * image_width + box['Width'] * image_width) * 1.10
        y2 = int(box['Top'] * image_height + box['Height'] * image_height) * 1.10
        image_crop = image.crop((x1, y1, x2, y2))

        stream = io.BytesIO()
        image_crop.save(stream, format="JPEG")
        image_crop_binary = stream.getvalue()

        pil_image = image_crop.convert('RGB')
        cropped = numpy.array(pil_image)
        # Convert RGB to BGR
        cropped = cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR)

        # Submit individually cropped image to Amazon Rekognition
        response = rekognition.search_faces_by_image(
            CollectionId='family_collection',
            Image={'Bytes': image_crop_binary}
        )
        print(response)
        if len(response['FaceMatches']) > 0:
            # Return results
            print('Coordinates ', box)
            for match in response['FaceMatches']:

                face = dynamodb.get_item(
                    TableName='PennappsXVIII',
                    Key={'RekognitionID': {'S': match['Face']['FaceId']}}
                )

                if 'Item' in face:
                    person = face['Item']['FullName']['S']
                else:
                    person = 'no match found'

                print(person)
                return match['Face']['FaceId'], match['Face']['Confidence'], person

        else:
            # Upload the new face as an unknown entity
            pass


@app.route('/googleactions', methods=['POST'])
def theGoog():
    data = request.args.to_dict()
    intentName = data['queryResult']['intent']['name']


if __name__ == '__main__':
    app.run(port=8080, debug=True)
