/** @type {import("prettier").Config} */
const config = {
  arrowParens: "always",
  trailingComma: "all",
  plugins: ["prettier-plugin-packagejson"],
};

module.exports = config;
