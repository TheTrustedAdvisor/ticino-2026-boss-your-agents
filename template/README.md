# Template

Everything the demo ran, with the tenant taken out. The main [README](../README.md) explains the five steps,
the prerequisites and what is not covered.

```bash
cp config.example.env config.env      # your workspaces, identities and token commands
python3 data/make_data.py             # ACCOUNT_MANAGERS=... puts a real user of your tenant first
./stage.sh /tmp/boss-your-agents      # session-1/, review/, session-2/, publish-wiki.sh, handover.sh
cd /tmp/boss-your-agents/session-1 && ./py tools/fab.py whoami
```

`stage.sh` never creates, empties or changes a workspace. Start with two empty ones and empty them yourself
between runs. Signing keys live in `~/.config/zero-to-hero/`, approved snapshots in
`~/.local/state/zero-to-hero/<workspace id>/`.

Offline checks that need no tenant:

```bash
cd /tmp/boss-your-agents/review
./py gate/role_guard.py --self-test                       # 14 cases of the role guard hook
./py gate/check_rules.py --lint <folder with rule files>  # rule schema, e.g. example-run/wiki/rules
```

The reviewers read the deployed state once per review round into `reports/run/state.json`. With the
recorded state of [../example-run/](../example-run/) copied there, `check_security.py`, `check_decisions.py
facts` and `check_rules.py` run without a tenant.
