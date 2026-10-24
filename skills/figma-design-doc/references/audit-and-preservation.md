# 链接核对和增量保留

## 本地检查命令

先通过工作区依赖加载工具取得 Python 路径，将其记为 `PYTHON_BIN`；`SKILL_DIR` 为当前技能目录。脚本只使用 Python 标准库，且不改写输入文件。

```sh
"$PYTHON_BIN" -B "$SKILL_DIR/scripts/audit_docx_links.py" output.docx
"$PYTHON_BIN" -B "$SKILL_DIR/scripts/audit_docx_links.py" output.docx --inventory inventory.json --json audit.json
"$PYTHON_BIN" -B "$SKILL_DIR/scripts/audit_docx_links.py" updated.docx --preserve-from before.docx
```

退出码 0 表示所请求的本地检查通过；1 表示发现链接、覆盖或保留问题；2 表示输入文件或清单无效。没有传入清单时，只能报告本地提取结果，不能声称页面无遗漏或 Figma 节点已在线核实。

## 独立清单

先从 Figma 建立清单，不从 DOCX 反推应有页面。以下为结构示例，值须换成当前任务实际读取的证据；不要把示例当成真实设计稿。

```json
{
  "scopes": [{"file_key": "ExampleFile", "node_id": "1:2"}],
  "targets": [
    {
      "file_key": "ExampleFile",
      "node_id": "1:2",
      "role": "entry",
      "scope_node_id": "1:2",
      "verified": true,
      "exists": true,
      "visible": true
    },
    {
      "file_key": "ExampleFile",
      "node_id": "10:20",
      "role": "page",
      "group": "搜索无结果",
      "version": "中文亮色",
      "scope_node_id": "1:2",
      "verified": true,
      "exists": true,
      "visible": true
    }
  ]
}
```

- `role` 可为 `page`、`annotation` 或 `entry`；清单记录实际需要直达链接的节点，不填包装层或普通图标。
- `group` 是页面或状态分组，`version` 是原稿存在的主题、语言等版本，不假定每组都是三版本。
- `verified`、`exists`、`visible` 来自当前读取证据。检查隐藏的组件变体时，使用 `visible: false` 并写明 `hidden_state_reason`，例如其确为被用户要求盘点的组件变体；脚本会在结果里单列，不将其表述为可见页面。
- `scope_node_id` 指向同一文件中用户指定的范围根节点。父子归属与语义仍须由执行者通过 Figma 读取证据核实，脚本只检查清单的一致性。
- 同一目标可在文档中作为入口和正文重复使用，结果会列出重复次数；需由执行者判断是否合理。清单以唯一目标做集合对照，不把重复引用自动视为错链。

工具返回信息应保留节点 ID、父层级、可见性、画布实际标题、版本和必要的状态证据。页面清单与标注清单分开统计，链接数量由最终文件计算。不要将“页面组数”“画板版本数”“标注组数”“链接出现次数”和“唯一链接目标数”混为一谈。

## 保留用户后来添加的内容

Word/WPS 可能在保存时将 `w:hyperlink` 转成 `w:fldSimple` 或一组 `w:fldChar`、`w:instrText` 域。只统计一种形式会把真实链接误判为丢失。脚本同时识别三种形式，且遍历正文、表格、页眉页脚和脚注等正文部件。

追加前读取磁盘最新文件，记录散列、原文、链接和需要保留的包部件；保留副本在任务证据目录。不要按上一轮文件大小或段落位置盲写。写回前再次校验散列，如文件发生变化，重新读取并合并本次追加，不能覆盖后来修改。

只追加文字时可只补丁修改 `word/document.xml`，保留其他 ZIP 部件的字节。原正文各元素、字段指令和关系应保持；在末尾 `sectPr` 前加入新内容即可。已有最后分页符时复用它，避免再添加分页导致空白页。新增标题跟随原文层级，核对结果不必附加批注或重写已有备注。

`--preserve-from` 检查原有 Figma 链接的文字和完整目标是否仍按原顺序出现，允许中间插入新链接。该检查不证明备注或正文未改；还需对比保留的正文元素和其他包部件，必要时比较原有页面渲染。

## 中文字体与分页

如果预览只剩数字、英文字母、下划线，或者中文显示方框，先检查渲染环境可用字体和 PDF 嵌入字体。文字提取成功不代表像素渲染正确。缺字可能改变页数，修好字体后再核对分页。

使用 documents 技能定位的捆绑 LibreOffice，不改用未授权的系统桌面实例。在确认系统存在可用中文字体后，可建立**任务临时** fontconfig 配置，通过 `FONTCONFIG_FILE` 仅提供给该次渲染。配置中的字体目录和缓存目录须从当前环境确认，不写入系统配置，不安装或清空共享字体缓存。不要将这次机器上的字体名称推广成所有环境必备字体。

修复字体后重新渲染，逐页确认汉字、分页和链接文字。渲染图片/PDF 为 QA 证据，除非用户要求，不作为额外交付物。
