## Description: <br>
Local search/indexing CLI (BM25 + vectors + rerank) with MCP mode. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[steipete](https://clawhub.ai/user/steipete) <br>

### License/Terms of Use: <br>


## Use Case: <br>
Developers and engineers use this skill to index local file collections and retrieve relevant content through keyword, vector, hybrid search, document lookup, or MCP mode. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill depends on an external qmd package source. <br>
Mitigation: Install only after verifying that the package source is trusted for the intended environment. <br>
Risk: Broad local collections can index sensitive files. <br>
Mitigation: Add narrow, intentional collection paths and exclude secrets or private directories from indexing. <br>
Risk: MCP mode or non-local Ollama endpoints can expose indexed content to tools or services outside the local process. <br>
Mitigation: Use MCP mode and remote Ollama endpoints only with trusted tools, servers, and network destinations. <br>


## Reference(s): <br>
- [qmd source package](https://github.com/tobi/qmd) <br>
- [Publisher homepage](https://tobi.lutke.com) <br>
- [ClawHub skill page](https://clawhub.ai/steipete/skills/qmd) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, Shell commands, Configuration guidance] <br>
**Output Format:** [Markdown with inline shell commands] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Guidance centers on qmd CLI commands, local indexing paths, Ollama endpoint configuration, and MCP mode.] <br>

## Skill Version(s): <br>
1.0.0 (source: release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
