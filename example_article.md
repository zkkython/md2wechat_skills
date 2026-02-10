# 欢迎使用微信公众号发布工具

![封面图片](https://picsum.photos/800/400?random=1)

这是一篇使用 wechatpy 官方 API 发布的示例文章。

## 功能特点

- **自动图片上传**：支持本地图片和远程图片 URL
- **Markdown 转换**：自动转换为微信公众号支持的 HTML
- **草稿箱发布**：安全地保存到草稿箱，不会自动群发

## 代码示例

```python
from wechatpy import WeChatClient

client = WeChatClient(appid, secret)
client.draft.add(articles=[article])
```

## 使用步骤

1. 配置 `.env` 文件，添加 `WECHAT_APPID` 和 `WECHAT_APP_SECRET`
2. 编写 Markdown 文章，第一张图片会自动作为封面
3. 运行发布命令：
   ```bash
   python wechat_official_api.py publish --markdown article.md
   ```

## 注意事项

- 标题最多 64 个字符
- 摘要最多 120 个字符
- 必须包含至少一张图片作为封面
- 文章保存为草稿，需要在公众平台后台手动发布

---

感谢使用微信公众号发布工具！
