import globals from "globals";
import pluginJs from "@eslint/js";
import tseslint from "typescript-eslint";
import pluginImport from "eslint-plugin-import";

export default [
  {
    files: ["**/*.{js,mjs,cjs,ts,jsx,tsx}"],
  },
  {
    languageOptions: {
      globals: { ...globals.node },
    },
  },

  pluginJs.configs.recommended,
  ...tseslint.configs.recommended,
  pluginImport.flatConfigs.recommended,
  pluginImport.flatConfigs.typescript,

  {
    rules: {
      curly: "error",

      "@typescript-eslint/no-require-imports": "off",
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
          ignoreRestSiblings: true,
          varsIgnorePattern: "^_",
        },
      ],

      // TODO: Turn back into a warning
      "@typescript-eslint/no-explicit-any": "off",

      "import/no-named-as-default": "off",
      "import/no-named-as-default-member": "off",
      "import/namespace": "off",
    },
    settings: {
      "import/resolver": {
        typescript: {
          alwaysTryTypes: true,
        },
      },
    },
  },
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parserOptions: {
        project: true,
      },
    },
    rules: {
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/consistent-type-exports": "error",
      "@typescript-eslint/consistent-type-imports": "error",
    },
  },
  {
    ignores: [
      "**.config.js",
      ".prettierrc.js",
      "build/**",
      "node_modules/**",
      "bin/**",
      "dist/**",
      "reference/mcp_capabilities_reference.json",
    ],
  },
];
