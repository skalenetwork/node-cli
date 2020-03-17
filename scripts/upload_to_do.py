import os
import sys
import boto3

session = boto3.session.Session()
LONG_LINE = '=' * 50


def print_info(endpoint_url, filename, space, key):
    print('Going to upload file...')
    print(f'''\
{LONG_LINE}
Endpoint: {endpoint_url}
Filename: {filename}
Space: {space}
Key: {key}
{LONG_LINE}
''')


def upload_file(access_key_id, secret_access_key, filename, space, key, region='sfo2',
                endpoint_url=None):
    if not endpoint_url:
        endpoint_url = f'https://{region}.digitaloceanspaces.com'
    print_info(endpoint_url, filename, space, key)
    client = session.client('s3',
                            region_name=region,
                            endpoint_url=endpoint_url,
                            aws_access_key_id=access_key_id,
                            aws_secret_access_key=secret_access_key)
    client.upload_file(filename, space, key, ExtraArgs={'ACL': 'public-read'})


if __name__ == "__main__":
    ACCESS_KEY_ID = os.environ['ACCESS_KEY_ID']
    SECRET_ACCESS_KEY = os.environ['SECRET_ACCESS_KEY']

    FILEPATH = sys.argv[1]
    SPACE_NAME = sys.argv[2]
    KEY = sys.argv[3]

    upload_file(ACCESS_KEY_ID, SECRET_ACCESS_KEY, FILEPATH, SPACE_NAME, KEY)
