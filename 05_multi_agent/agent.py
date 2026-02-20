"""エージェント定義 (Agent Engine デプロイ用エントリーポイント)。

Agent Engine にデプロイする場合、このモジュールの root_agent が使用される。
"""

from .pipeline import root_agent  # noqa: F401
