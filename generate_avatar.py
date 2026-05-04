import os
import base64
import uuid
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_partner_avatar(prompt):
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )

    image_base64 = response.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    os.makedirs("static/avatars", exist_ok=True)

    filename = f"{uuid.uuid4()}.png"
    file_path = os.path.join("static", "avatars", filename)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return f"/static/avatars/{filename}"