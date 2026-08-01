# Output

```text
output/
  submission/             # 实际上传或待上传的最终投稿文件
  outreach/               # 厂商沟通、问题反馈和邮件草稿
  qa/                     # 日志、PDF 渲染图、LaTeX 中间文件等可重建材料
```

三个子目录都只保存本地工作材料，默认不进入公开 Git 仓库：

- `submission/` 可能包含在审稿件和 CMT 实际上传文件；
- `outreach/` 可能包含联系人与厂商沟通内容；
- `qa/` 是可重建的检查材料。

需要公开的定稿应在录用或正式发布后，经单独检查再复制到合适的 release 目录。
