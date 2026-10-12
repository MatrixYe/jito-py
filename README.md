# jito-py

**Jito searcher JSON-RPC API 的 Python 客户端——提交 Solana bundle、查询 bundle 状态、
发现 block-engine 端点。**

已发布到 PyPI：[`jito-py`](https://pypi.org/project/jito-py/)。

![python](https://img.shields.io/badge/Python-%3E%3D3.10-3776ab) ![pypi](https://img.shields.io/badge/pypi-jito--py%200.1.3-blue) ![license](https://img.shields.io/badge/license-MIT-green)

---

## 为什么有这个项目

Jito 的 searcher API 是 Solana MEV 的入口：bundle 会被原子化排序，而你附加的 tip
决定了能不能买到那个 slot。官方接口是 Rust 的（`jito-solana`、`searcher-examples`），
而研究栈和策略栈基本都是 Python。

`jito-py` 就是这座薄桥——它不隐藏 RPC，只是省掉手写 JSON-RPC 信封和无类型 dict 字符串解析
的麻烦。

---

## 安装

```bash
pip install jito-py
```

需要 Python 3.10+（模块使用了 PEP 604 的 `X | None` 联合类型语法）。

## 使用

### 1. 发现 block-engine 端点

```python
from jito_py.block_engine import BlockEngine

engines = BlockEngine.get_block_engines(network="mainnet")
for region, info in engines.items():
    print(region, info["block_engine_url"], info["shred_receiver_addr"])
```

| 网络 | 区域 |
|---|---|
| `mainnet` | Amsterdam、Frankfurt、York（纽约）、Tokyo |
| `testnet` | Dallas、York（纽约） |

每个条目包含 `block_engine_url`（HTTPS RPC）、`shred_receiver_addr`（UDP，`host:1002`）
和 `relayer_url`。选离你的验证者或自有基础设施最近的区域——
bundle 延迟由网络距离主导，不是 CPU。

### 2. 以 searcher 身份调用

```python
from jito_py.searcher import Searcher

searcher = Searcher("https://ny.mainnet.block-engine.jito.wtf")

# tip 账户属于当前 epoch，会轮换。每次都要重新取。
tip_accounts = searcher.get_tip_accounts()

# 最多 5 笔已完整签名、base58 编码的交易，作为一个原子 bundle 提交。
bundle_id = searcher.send_bundle(["<base58-signed-tx>", "..."])

# 轮询状态
resp = searcher.get_bundle_statuses([bundle_id])
print(resp.context_slot)
for status in resp.statuses:
    print(status.bundle_id, status.slot, status.confirmation_status, status.err)

# 单笔交易代理：以 bundle 形式提交，并附带 Jito 赞助的最低 tip。
tx_id = searcher.send_transaction("<base58-signed-tx>")
```

### 接口清单

| 方法 | Jito 方法名 | 端点 |
|---|---|---|
| `get_tip_accounts()` | `getTipAccounts` | `/api/v1/bundles` |
| `get_bundle_statuses(bundle_ids)` | `getBundleStatuses` | `/api/v1/bundles` |
| `send_bundle(transactions)` | `sendBundle` | `/api/v1/bundles` |
| `send_transaction(transaction)` | `sendTransaction` | `/api/v1/transactions` |

`get_bundle_statuses` 返回类型化对象，而不是 dict：

```python
@dataclass
class BundleStatus:
    bundle_id: str
    transactions: List[str]
    slot: int
    confirmation_status: str
    err: Dict[str, Any]

@dataclass
class BundleStatusesResponse:
    context_slot: int
    statuses: List[BundleStatus]
```

---

## 关键工程决策

| 决策 | 理由 |
|---|---|
| **响应用 dataclass 类型化** | bundle 状态是异步填充的，也正是 searcher 会循环轮询的值。属性访问胜过 `resp["result"]["value"][0]["confirmation_status"]`——后面这条链就是一个等着变成静默 `None` 的拼写错误。 |
| **所有调用共用一个 `_send_rpc_request`** | JSON-RPC 信封（`jsonrpc: "2.0"`、`id: 1`、`params`）在各方法间完全一致，只有 `method` 和 URL 路径不同。加超时、重试、日志时只需要改一个地方。 |
| **`_extract_result` 在缺少 `result` 时直接抛错** | Jito 会用 HTTP 200 返回 `error` 字段。静默返回 `None` 会在好几层之后才变成一个 `TypeError`；在边界处失败能把出问题的方法名直接点出来。 |
| **解析前先 `response.raise_for_status()`** | HTTP 层失败不能被当成 JSON-RPC 错误来解析。 |
| **`rstrip("/") + "/" + lstrip("/")` 拼接 URL** | `block_engine_url` 由用户传入，可能带也可能不带结尾斜杠。两种写法都要能用。 |
| **同一个类上挂两个 base URL** | bundle 在 `/api/v1/bundles`，单笔交易在 `/api/v1/transactions`。同一个 host、不同路径——一个类搞定，不用复制客户端。 |
| **测试 mock 掉 `requests.post`** | 测试断言请求构造与响应解析，零网络访问，所以能在 CI 里跑，也能离线跑。 |
| **`setuptools` + `pyproject.toml`，版本只维护一处** | 发版流程就是 `make build` → `make upload`（twine）。`setup.py` 只是一个两行的壳。 |

---

## 开发

```bash
git clone https://github.com/MatrixYe/jito-py && cd jito-py
pip install -r requirements.txt

# 单元测试——不需要网络
python -m unittest discover -s tests -v

# 构建 wheel / sdist
make build

# 发布到 PyPI
make upload
```

---

## 技术栈

```
语言       Python（标准库 dataclasses + typing）
HTTP       requests
打包       setuptools + pyproject.toml（PEP 621）、python -m build、twine
测试       unittest + unittest.mock
```

---

## 局限与已知缺口

- **只有 2 个单元测试**（`get_tip_accounts`、`get_bundle_statuses`）。
  `send_bundle` 和 `send_transaction` 没有测试——而恰恰是这两个最关键。
- **没有 CI。** 没有 GitHub Actions workflow，也没有可展示的徽章；
  测试只有在有人手动跑的时候才会跑。
- **没有超时，也没有重试。** `requests.post` 调用时没有传 `timeout`，
  连接挂住就会永远阻塞。对一个低延迟的 MEV 客户端来说这是最该先修的一条。
- **`bundleOnly=true` 有文档但用不了。** `send_transaction` 的 docstring 解释了
  这个参数，但 `_send_rpc_request` 根本不接受查询参数。
- **没有异步客户端。** searcher 轮询 bundle 状态需要的是 `aiohttp`/`httpx`，
  而不是每次调用占一个阻塞 socket。
- **没有 tip 逻辑。** `get_tip_accounts` 返回账户列表，但没有任何代码会选一个账户、
  定 tip 金额，或者构造 tip 指令——这些完全留给调用方。
- **没有 base58 工具函数。** 输入输出都是原始字符串，编解码要调用方自己做。
- **`requires-python` 写错了。** `pyproject.toml` 声明 `>=3.6`，但代码需要 3.10+
  （PEP 604 联合类型）。下次发版前应修正。
- **`jito_py/__init__.py` 是空的**，所以 `from jito_py import Searcher` 不能用——
  必须走 `jito_py.searcher` / `jito_py.block_engine`。把公开名字重新导出，
  才符合使用者的预期。
- **端点元数据是硬编码的**（block-engine 区域、relayer URL）。Jito 会改动这些；
  目前既没有运行时校验，也没有自我更新机制。

### 后续计划

1. 给 `_send_rpc_request` 加 `timeout` 与重试/退避；暴露 `bundleOnly` 参数。
2. 为 `send_bundle` / `send_transaction` 补测试，并加 CI workflow。
3. 提供异步版 `Searcher`，与现有请求/解析核心复用。
4. 修正 `requires-python`，并在 `__init__.py` 里补上重新导出。
