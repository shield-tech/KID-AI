from kid.memory import MemoryStore


def test_memory_round_trip(tmp_path):
    store = MemoryStore(tmp_path / "kid-memory.db")
    store.add_conversation_turn("user", "hello")
    store.add_conversation_turn("assistant", "hi")
    notes = store.get_recent_messages()
    assert len(notes) == 2
    assert notes[0]["role"] == "user"

    note_id = store.add_note("Reminder", "Back up the project")
    found = store.search_memory("backup")
    assert found[0]["id"] == note_id

    store.set_preference("theme", "dark")
    assert store.get_preference("theme") == "dark"


def test_memory_can_delete_note(tmp_path):
    store = MemoryStore(tmp_path / "kid-memory.db")
    note_id = store.add_note("Draft", "test text")
    store.delete_note(note_id)
    assert store.list_notes() == []
