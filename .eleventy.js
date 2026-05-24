module.exports = function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy("content/assets");

  return {
    dir: {
      input: "content",
      output: "dist",
      includes: "_includes",
      layouts: "_includes/layouts",
    },
  };
};
