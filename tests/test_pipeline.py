from sekai.cli import run
from conftest import (
    FakeAnthropicClient,
    FakeRedditClient,
    make_submission,
    make_synthesis_payload,
    reddit_link,
)


def test_end_to_end_pipeline_writes_grounded_report(
    tmp_path, all_credentials, override_reddit_client, override_anthropic_client
):
    submissions = [
        make_submission(
            id="abc123",
            title="Ramen tourism is booming in Tokyo",
            selftext="Visitors are lining up for ramen shops more than ever this year.",
            score=120,
            link_suffix="ramen_tourism",
        ),
        make_submission(
            id="def456",
            title="Some locals are annoyed by ramen tourists",
            selftext="Long lines are frustrating regulars at small ramen shops.",
            score=45,
            link_suffix="ramen_backlash",
        ),
    ]
    link_1 = reddit_link("abc123", "ramen_tourism")
    link_2 = reddit_link("def456", "ramen_backlash")

    response = make_synthesis_payload(
        topic="ramen tourism",
        views=[
            {
                "stance": "Pro-tourism",
                "summary_ja": "観光客の増加は店の収益に良い影響を与えている。",
                "source": "reddit",
                "link": link_1,
                "why_surprising": None,
            },
            {
                "stance": "Local backlash",
                "summary_ja": "常連客は行列の長さに不満を持っている。",
                "source": "reddit",
                "link": link_2,
                "why_surprising": "観光公害への懸念は日本国内の議論にも通じる。",
            },
        ],
    )

    override_reddit_client(FakeRedditClient(submissions))
    fake_llm = FakeAnthropicClient(response)
    override_anthropic_client(fake_llm)

    out_path = tmp_path / "report.md"
    exit_code = run(["--topic", "ramen tourism", "--out", str(out_path)])

    assert exit_code == 0
    assert out_path.exists()

    report = out_path.read_text(encoding="utf-8")
    assert "ramen tourism" in report
    assert "概ね好意的に受け止められている。" in report
    assert "観光客の増加を歓迎する声と、混雑を嫌がる声がある。" in report
    assert "Pro-tourism" in report
    assert link_1 in report
    assert "Local backlash" in report
    assert link_2 in report
    assert fake_llm.call_count == 1


def test_zero_fetch_results_aborts_before_synthesize(
    tmp_path, all_credentials, override_reddit_client, override_anthropic_client, capsys
):
    override_reddit_client(FakeRedditClient([]))
    fake_llm = FakeAnthropicClient(make_synthesis_payload("topic", []))
    override_anthropic_client(fake_llm)

    out_path = tmp_path / "report.md"
    exit_code = run(["--topic", "an extremely obscure topic", "--out", str(out_path)])

    assert exit_code == 1
    assert not out_path.exists()
    assert fake_llm.call_count == 0
    assert "Error" in capsys.readouterr().err


def test_malformed_llm_json_raises_clear_error(
    tmp_path, all_credentials, override_reddit_client, override_anthropic_client, capsys
):
    submissions = [
        make_submission(
            id="abc123",
            title="A topic with real discourse",
            selftext="This text is long enough to survive curation's length filter.",
            score=10,
            link_suffix="real_discourse",
        ),
    ]
    override_reddit_client(FakeRedditClient(submissions))
    override_anthropic_client(FakeAnthropicClient("not valid json"))

    out_path = tmp_path / "report.md"
    exit_code = run(["--topic", "a topic", "--out", str(out_path)])

    assert exit_code == 1
    assert not out_path.exists()
    assert "invalid JSON" in capsys.readouterr().err


def test_missing_reddit_credentials_fails_before_network_call(
    tmp_path, anthropic_credentials, override_anthropic_client, capsys, monkeypatch
):
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("REDDIT_USER_AGENT", raising=False)

    out_path = tmp_path / "report.md"
    exit_code = run(["--topic", "a topic", "--out", str(out_path)])

    assert exit_code == 1
    assert not out_path.exists()
    assert "Reddit credentials" in capsys.readouterr().err


def test_invalid_sources_value_fails_fast(capsys):
    exit_code = run(["--topic", "a topic", "--sources", "twitter"])

    assert exit_code == 1
    assert "Unsupported source" in capsys.readouterr().err


def test_invalid_model_value_fails_fast(capsys):
    exit_code = run(["--topic", "a topic", "--model", "qwen"])

    assert exit_code == 1
    assert "Unsupported model" in capsys.readouterr().err
