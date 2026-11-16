/* Locally bundled Markdown rendering; model output must never enable raw HTML. */
const replyFormatter = (() => {
  const markdown = new markdownit({ html: false, linkify: true, breaks: true });
  // Replies can cite web pages, but cannot load images or use active/local URLs.
  markdown.disable("image");
  markdown.linkify.set({ fuzzyLink: false, fuzzyEmail: false });
  markdown.validateLink = value => {
    try { return ["http:", "https:"].includes(new URL(value).protocol); }
    catch (_) { return false; }
  };
  markdown.renderer.rules.link_open = (tokens, index, options, env, renderer) => {
    tokens[index].attrSet("target", "_blank");
    tokens[index].attrSet("rel", "noopener noreferrer");
    return renderer.renderToken(tokens, index, options);
  };
  markdown.renderer.rules.table_open = () =>
    '<div class="reply-table" role="region" aria-label="Comparison table" tabindex="0"><table>\n';
  markdown.renderer.rules.table_close = () => '</table></div>\n';
  return { render: value => markdown.render(value) };
})();
