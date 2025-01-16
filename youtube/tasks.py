from celery import shared_task


@shared_task
def test_task(word:str):
    return f'hello {word}'


