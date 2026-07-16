from pyhive import HiveClient
from pyhive.types import Module, Queue, User


def test_create_queue_for_module(client: HiveClient, module: Module):
    queue = client.create_queue(
        "TestQueue123",
        module=module,
    )
    assert queue is not None
    assert isinstance(queue, Queue)
    queue.delete()


def test_create_queue_for_student(client: HiveClient, student: User):
    queue = client.create_queue(
        "TestQueue123",
        user=student,
    )
    assert queue is not None
    assert isinstance(queue, Queue)
    queue.delete()
