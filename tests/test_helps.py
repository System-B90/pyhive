from pyhive.client import HiveClient
from pyhive.src.types.help_ import Help
from pyhive.src.types.help_response import HelpResponse


def test_get_help_requests(client: HiveClient):
    helps = list(client.get_help_requests(limit=10))
    assert isinstance(helps, list)
    if helps:
        assert all(isinstance(h, Help) for h in helps)


def test_get_help_request_by_id(client: HiveClient):
    helps = list(client.get_help_requests(limit=1))
    if not helps:
        return
    h = helps[0]
    looked_up = client.get_help_request(h.id)
    assert isinstance(looked_up, Help)
    assert looked_up.id == h.id


def test_get_help_responses_and_response_by_id(client: HiveClient):
    helps = list(client.get_help_requests(limit=3))
    if not helps:
        return
    for h in helps:
        responses = list(client.get_help_responses(h.id))
        assert isinstance(responses, list)
        if responses:
            assert all(isinstance(r, HelpResponse) for r in responses)
            resp = client.get_help_response(h.id, responses[0].id)
            assert isinstance(resp, HelpResponse)
            assert resp.id == responses[0].id
            break


def test_get_help_response_student_files(client: HiveClient):
    helps = list(client.get_help_requests(limit=3))
    if not helps:
        return
    for h in helps:
        responses = list(client.get_help_responses(h.id))
        if not responses:
            continue
        files = client.get_help_response_student_files(h.id, responses[0].id)
        assert isinstance(files, list)
        if files:
            assert isinstance(files[0], dict)
        break


def test_create_and_delete_new_chat(client: HiveClient) -> None:
    student = list(client.get_students())[0]
    CHAT_TITLE = f"Test Chat with {student.first_name}"
    chat = client.create_chat(with_user=student, title=CHAT_TITLE)
    try:
        assert chat.title == CHAT_TITLE
    finally:
        client.delete_chat(chat)
