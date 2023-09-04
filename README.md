# BlueSky Cross-Poster

This is a simple cross-poster that is designed for making posts across both BlueSky and Mastodon easier and more streamlined. It is designed to be used to only link your BlueSky account to your Mastodon account, and not to link your Mastodon account to your BlueSky account. This is to prevent any potential issues with imposing on user's privacy.

## Installation

You can install this project by running the following commands or using the Docker image.

```
git clone https://git.hack13.dev/hack13/BlueSky-Cross-Poster.git
cd BlueSky-Cross-Poster
pip install -r requirements.txt
python app.py
```

Or you can use the Docker image by running the following commands.

```
docker run -d -p 5000:5000 git.hack13.dev/hack13/blusky-cross-poster:latest \
    -e PORT=5000 \
    -e API_KEY='your_api_key' \
    -e FERNET_KEY='your_fernet_key' \
```

## Usage

To use this application you will need to have a BlueSky account and know how to generate an App Password. You will also need to know how to generate yourself an access token with Read and Write permissions. You will also need to generate a Fernet Key, there is a built in function to generate one.

If you are not using the Docker image you will need to set the following environment variables.

```
API_KEY='your_api_key'
FERNET_KEY='your_fernet_key'
PORT=5000
```

How to generate an App Password: https://docs.bluesky.social/faq.html#how-do-i-generate-an-app-password

How to generate an access token: https://docs.joinmastodon.org/api/authentication/

How to generate a Fernet Key: YOURAPI:5000/api/v1/createKey

How to Add Your User: YOURAPI:5000/api/v1/createUser

1. Set your header for 'X-API-KEY' to your API Key
2. Send a POST with form data of:
3. 'atProtoUser' to your BlueSky Handle
4. 'atAppPassword' to your BlueSky App Password
5. 'mastodonToken' to your generated Mastodon Token
6. 'mastodonInstance' to your Mastodon Instance URL (ex: https://mastodon.social)

How to Fetch Posts from BlueSky: YOURAPI:5000/api/v1/runAtProtoFetcher

1. Set your header for 'X-API-KEY' to your API Key

How to Fetch Posts from Mastodon: YOURAPI:5000/api/v1/runMastoFetcher

1. Set your header for 'X-API-KEY' to your API Key

How to Post to BlueSky: YOURAPI:5000/api/v1/postToAtProto

1. Set your header for 'X-API-KEY' to your API Key

How to Post to Mastodon: YOURAPI:5000/api/v1/postToMastodon

1. Set your header for 'X-API-KEY' to your API Key

## Contributing

Please feel free to contribute to this project. If you have any questions please feel free to reach out to me on Mastodon @hack13@cyberfurz.social or on BlueSky @hack13.me

## License

MIT License
