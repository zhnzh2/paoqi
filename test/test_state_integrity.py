from core.game import Game

def _reach_pending_auto_action() -> Game:
    game = Game()

    for _ in range(20):
        if game.has_pending_auto_action():
            return game

        actions = game.get_legal_actions()
        assert actions
        game.apply_action(actions[0])

    raise AssertionError("did not reach a pending auto action")

def test_undo_clears_pending_auto_action_created_by_reverted_move() -> None:
    game = _reach_pending_auto_action()

    game.undo()

    assert not game.has_pending_auto_action()
    assert game.pending_auto_action is None
    assert game.pending_auto_message == ""
    assert all(game.is_action_legal(action) for action in game.get_legal_actions())

def test_undo_confirmed_pending_auto_action_restores_confirmation_state() -> None:
    game = _reach_pending_auto_action()
    pending = game.pending_auto_action
    pending_message = game.pending_auto_message

    assert pending is not None
    game.apply_action(pending)
    game.undo()

    assert game.pending_auto_action == pending
    assert game.pending_auto_message == pending_message

def test_export_import_preserves_terminal_reason_and_pending_auto_action() -> None:
    finished = Game()
    finished.finish_game("agreement")

    restored_finished = finished.clone()
    assert restored_finished.game_over_reason == "agreement"

    pending_game = _reach_pending_auto_action()
    restored_pending = pending_game.clone()

    assert restored_pending.pending_auto_action == pending_game.pending_auto_action
    assert restored_pending.pending_auto_message == pending_game.pending_auto_message


def test_score_uses_piece_count_not_piece_levels() -> None:
    game = Game()

    game.apply_action(
        {
            "type": "move",
            "mode": "upgrade",
            "x": 9,
            "y": 9,
        }
    )

    assert game.calculate_score()[0] == 1


def test_clone_does_not_share_pending_auto_action_dict() -> None:
    game = _reach_pending_auto_action()
    clone = game.clone()

    assert clone.pending_auto_action == game.pending_auto_action
    assert clone.pending_auto_action is not game.pending_auto_action
