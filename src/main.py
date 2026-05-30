import json
import boto3
import urllib.parse
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('s3-trigger-db')

def lambda_handler(event, context):
    print("Event:", json.dumps(event))

    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(record['s3']['object']['key'])

    logger.info(f"Fichier reçu : s3://{bucket}/{key}")

    try:
        table.put_item(
            Item={
                'PK': key,        # ✅ correspond à la partition key de ta table
                'bucket': bucket,
            },
            ConditionExpression='attribute_not_exists(PK)'  # ✅ même nom
        )
        logger.info(f"✅ Nouveau fichier enregistré : {key}")
        return {
            'statusCode': 200,
            'body': json.dumps(f'Fichier traité : {key}')
        }

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning(f"⛔ Doublon détecté, ignoré : {key}")
            return {
                'statusCode': 409,
                'body': json.dumps(f'Fichier déjà traité : {key}')
            }
        raise