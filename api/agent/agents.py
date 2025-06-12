import os
import io
import base64
import json
from typing import Annotated

import aiohttp
from api.agent.decorators import agent
from api.model import AgentUpdateEvent, Content
from api.agent.storage import save_image_blobs
from api.agent.common import execute_foundry_agent, post_request
from typing import Annotated
import uuid
import tweepy
from api.agent.storage import get_storage_client
import requests                 # ← keep, still used for the image GET

# Twitter Auth (use environment variables for secrets)
TW_API_KEY = os.environ.get("TW_API_KEY", "")
TW_API_SECRET = os.environ.get("TW_API_SECRET", "")
TW_ACCESS_TOKEN = os.environ.get("TW_ACCESS_TOKEN", "")
TW_ACCESS_TOKEN_SECRET = os.environ.get("TW_ACCESS_TOKEN_SECRET", "")
TW_BEARER_TOKEN = os.environ.get("TW_BEARER_TOKEN", "")


AZURE_IMAGE_ENDPOINT = os.environ.get("AZURE_IMAGE_ENDPOINT", "EMPTY").rstrip("/")
AZURE_IMAGE_API_KEY = os.environ.get("AZURE_IMAGE_API_KEY", "EMPTY")


@agent(
    name="Image Generation Agent",
    description="This agent can generate a number of images based upon a detailed description. This agent is based on the GPT-Image-1 model and is capable of generating images in a variety of styles. It can also generate images in a specific style, such as a painting or a photograph. The agent can also generate images with different levels of detail and complexity.",
)
async def gpt_image_generation(
    description: Annotated[
        str,
        "The detailed description of the image to be generated. The more detailed the description, the better the image will be. Make sure to include the style of the image, the colors, and any other details that will help the model generate a better image.",
    ],
    n: Annotated[int, "number of images to generate"],
    notify: AgentUpdateEvent,
) -> list[str]:

    await notify(
        id="image_generation",
        status="run in_progress",
        information="Starting image generation",
    )

    size: str = "1024x1024"
    quality: str = "low"
    api_version = "2025-04-01-preview"
    deployment_name = "gpt-image-1"
    endpoint = f"{AZURE_IMAGE_ENDPOINT}/openai/deployments/{deployment_name}/images/generations?api-version={api_version}"

    await notify(
        id="image_generation", status="step in_progress", information="Executing Model"
    )

    async with post_request(
        endpoint,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AZURE_IMAGE_API_KEY}",
        },
        json={
            "prompt": description,
            "size": size,
            "quality": quality,
            "output_compression": 100,
            "output_format": "png",
            "n": n,
        },
    ) as response:
        if "error" in response:
            print(response["error"])
            await notify(
                id="image_generation",
                status="step failed",
                information=response["error"],
            )
            return []

        await notify(
            id="image_generation",
            status="step in_progress",
            information="fetching images" if n > 1 else "fetching image",
        )

        # save the image to a file
        # iterate through the images and save them
        if not response["data"]:
            print("No images found in the response.")
            return []

        await notify(
            id="image_generation",
            status="step in_progress",
            information="storing images" if n > 1 else "storing image",
        )

        base64_images = [
            item["b64_json"] for item in response["data"] if item["b64_json"]
        ]

        images = []
        async for blob_name in save_image_blobs(base64_images):
            images.append(blob_name)
            await notify(
                id="image_generation",
                status="step completed",
                content=Content(
                    type="image",
                    content=[
                        {
                            "type": "image",
                            "description": description,
                            "size": size,
                            "quality": quality,
                            "image_url": blob_name,
                        }
                    ],
                ),
                output=True,
            )

        await notify(
            id="image_generation",
            status="run completed",
            information="Image generation complete",
        )

        return images


@agent(
    name="Image Editing Agent",
    description="""
    This tool can edit an image based upon a detailed description and a provided image. 
    Trigger this tool with a description of the edit to be made along with
    a kind parameter that indicates whether the image is a file upload
    or a camera capture. The image will be used as a starting point for the edit.
    The more detailed the description, the better the image will be.
    The image itself will be automatically provided as a file or a camera capture,
    so you do not need to include the image in the request. If the user is uploading a file, 
    set the kind to "FILE" - the user will explictly mention an "upload". If the user is 
    capturing an image with their camera, set the kind to "CAMERA" - the user will explicitly 
    mention a "camera capture" or say "take a picture". IMPORTANT: Do not ask the user to upload an image,
    or to take a picture, as soon as you issue the function call the UI will handle this for 
    you based on the kind parameter - it is important that you do not ask the user to upload an image or take a picture,
    as this will cause the UI to not work correctly - just provide the description and the kind parameter.
    The image will be edited based on the description provided.
    """,
)
async def gpt_image_edit(
    description: Annotated[
        str,
        "The detailed prompt of image to be edited. The more detailed the description, the better the image will be. Make sure to include the style of the image, the colors, and any other details that will help the model generate a better image.",
    ],
    image: Annotated[
        str,
        "The base64 encoded image to be used as a starting point for the generation. You do not need to include the image itself, you can add a placeholder here since the UI will handle the image upload.",
    ],
    kind: Annotated[
        str,
        'This can be either a file upload or an image that is captured with the users camera. Choose "FILE" if the image is uploaded from the users device. Choose "CAMERA" if the image should be captured with the users camera.',
    ],
    notify: AgentUpdateEvent,
) -> list[str]:
    await notify(
        id="image_edit",
        status="run in_progress",
        information="Starting image edit",
    )

    api_version = "2025-04-01-preview"
    deployment_name = "gpt-image-1"
    endpoint = f"{AZURE_IMAGE_ENDPOINT}/openai/deployments/{deployment_name}/images/edits?api-version={api_version}"

    await notify(
        id="image_edit", status="step in_progress", information="Executing Model"
    )

    size: str = "1024x1024"
    quality: str = "low"

    # send image as multipart/form-data
    if image.startswith("data:image/jpeg;base64,"):
        image = image.replace("data:image/jpeg;base64,", "")
        
    form_data = aiohttp.FormData()
    img = io.BytesIO(base64.b64decode(image))
    form_data.add_field("image", img, filename="image.jpg", content_type="image/jpeg")
    form_data.add_field("prompt", description, content_type="text/plain")
    form_data.add_field("size", size, content_type="text/plain")
    form_data.add_field("quality", quality, content_type="text/plain")

    async with post_request(
        endpoint,
        headers={
            "Authorization": f"Bearer {AZURE_IMAGE_API_KEY}",
        },
        data=form_data,
    ) as response:
        if "error" in response:
            print(json.dumps(response, indent=2))
            await notify(
                id="image_generation",
                status="step failed",
                information=response["error"],
            )
            return []

        await notify(
            id="image_edit",
            status="step in_progress",
            information="fetching image",
        )

        # save the image to a file
        # iterate through the images and save them
        if not response["data"]:
            print("No images found in the response.")
            return []

        await notify(
            id="image_edit",
            status="step in_progress",
            information="storing image",
        )

        base64_images = [
            item["b64_json"] for item in response["data"] if item["b64_json"]
        ]

        images = []
        async for blob in save_image_blobs(base64_images):
            images.append(blob)
            await notify(
                id="image_edit",
                status="step completed",
                content=Content(
                    type="image",
                    content=[
                        {
                            "type": "image",
                            "description": description,
                            "image_url": blob,
                            "kind": kind,
                        }
                    ],
                ),
                output=True,
            )

        await notify(
            id="image_edit",
            status="run completed",
            information="Image edit complete",
        )

        return images


@agent(
    name="BuildEvents - Post to LinkedIn Agent - Local",
    description="""
You are a publishing agent responsible for posting finalized and approved LinkedIn posts. 

You will receive as input:
- title (string): Title of the post.
- content (string): Body of the post or finalized draft.
- image_url (string, optional): Format should always start with https://sustineo-api.jollysmoke-a2364653.eastus2.azurecontainerapps.io/images/
- example image_url: https://sustineo-api.jollysmoke-a2364653.eastus2.azurecontainerapps.io/images/acd7fe97-8d22-48ca-a06c-d38b769a8924.png
- use the provided image_url

You will take the draft and publish the post on LinkedIn by calling the OpenAPI tool.""",
)
async def publish_linkedin_post(
    content: Annotated[str, "Body of the post or finalized draft in markdown."],
    image_url: Annotated[
        str,
        "Format should always start with https://sustineo-api.jollysmoke-a2364653.eastus2.azurecontainerapps.io/images/",
    ],
    notify: AgentUpdateEvent,
):
    instructions = f"""
Use the following `image_url`: {image_url}
Use this `image_url` exactly as it is. Do not change the image_url or the content of the post.
The post should be in markdown format.
"""
    await execute_foundry_agent(
        agent_id="asst_MbvKNQxeTr5DL1wuE8DRYR3M",
        additional_instructions=instructions,
        query=f"Can you write a LinkedIn post based on the following content?\n\n{content}",
        tools={},
        notify=notify,
    )


@agent(
    name="Post Tweet with Image",
    description="""
        Posts a tweet with an image to Twitter. 
        You will receive as input:
        - content (string): Body of the post or finalized draft.
        - image_url (string, optional): Format should always start with https://sustineo-api.jollysmoke-a2364653.eastus2.azurecontainerapps.io/images/
        - example image_url: https://sustineo-api.jollysmoke-a2364653.eastus2.azurecontainerapps.io/images/acd7fe97-8d22-48ca-a06c-d38b769a8924.png
        - use the provided image_url
    """
)
async def post_tweet_with_image(
    image_url: Annotated[
        str,
        "Format should always start with https://sustineo-api.jollysmoke-a2364653.eastus2.azurecontainerapps.io/images/",
    ],
    content: Annotated[str, "Text of the tweet (max 280 chars)"],
    notify: AgentUpdateEvent,
):
    await notify(id="post_tweet_image", status="run in_progress", information="Downloading image …")

    # ------------------------------------------------------------------
    # Setp 1: Download the Image
    # OAuth 1.0a session – used for BOTH upload and status update
    # ------------------------------------------------------------------
    auth_v1 = tweepy.OAuth1UserHandler(
        TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_TOKEN_SECRET
    )
    api_v1 = tweepy.API(auth_v1, wait_on_rate_limit=True)

    # Download the image ------------------------------------------------
    await notify(
    id="post_tweet_image",
    status="run in_progress",
    information="Downloading image …"
    )

    try:
        image_response = requests.get(image_url, timeout=10)
        image_response.raise_for_status()

        with open("temp_image_upload.png", "wb") as f:
            f.write(image_response.content)

        await notify(
            id="post_tweet_image",
            status="step completed",
            information="Image downloaded"
        )

    except Exception as exc:
        await notify(
            id="post_tweet_image",
            status="run failed",
            information=f"Failed to download image: {exc}"
        )

    
    # ------------------------------------------------------------------
    # Setp 2: Upload the Image to Twitter
    # OAuth 1.0a session – used to upload media to Twitter/X. This is required
    # ------------------------------------------------------------------
    await notify(id="post_tweet_image",
                 status="step in_progress",
                 information="Uploading image to Twitter …")

    try:
        media = api_v1.media_upload("temp_image_upload.png")
        media_id = media.media_id_string
    except Exception as exc:
        await notify(
            id="post_tweet_image",
            status="run failed",
            information=f"Error uploading image: {exc}",
        )
        return

    await notify(id="post_tweet_image",
                 status="step completed",
                 information="Image uploaded")
    
    # ------------------------------------------------------------------
    # Step 3: Post the Tweet with the Image
    # Post tweet (v2 – OAuth 2.0 user-context). Required to use OAth 2.0
    # ------------------------------------------------------------------
    await notify(id="post_tweet_image", status="step in_progress", information="Posting tweet …")

    payload = {"text": content, "media": {"media_ids": [media_id]}}
    headers = {
        "Authorization": f"Bearer {TW_BEARER_TOKEN}",
        "Content-Type": "application/json",
    }
    resp = requests.post("https://api.twitter.com/2/tweets", headers=headers, json=payload)

    if resp.status_code not in (200, 201):
        await notify(
            id="post_tweet_image",
            status="run failed",
            information=f"Error posting tweet: {resp.text}",
        )
        return

    tweet_id = resp.json().get("data", {}).get("id", "")
    tweet_url = f"https://x.com/i/web/status/{tweet_id}" if tweet_id else "(tweet created)"

    await notify(
        id="post_tweet_image",
        status="run completed",
        information="Tweet posted!",
        content=Content(type="text", content=[{"type": "text", "value": f"Tweeted: {tweet_url}"}]),
        output=True,
    )
