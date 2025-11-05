import pluginVue from 'eslint-plugin-vue'

export default [
  // Vue 推荐规则
  ...pluginVue.configs['flat/recommended'],
  
  {
    files: ['**/*.{js,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
        console: 'readonly',
        process: 'readonly',
        __dirname: 'readonly',
        FormData: 'readonly',
        Blob: 'readonly',
        URL: 'readonly',
        fetch: 'readonly',
        ElMessage: 'readonly',
        ElMessageBox: 'readonly',
      },
    },
    rules: {
      // Vue 规则
      'vue/multi-word-component-names': 'off',
      'vue/no-v-html': 'warn',
      'vue/require-default-prop': 'off',
      'vue/require-prop-types': 'off',
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      
      // JavaScript 规则
      'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      'prefer-const': 'warn',
      'no-var': 'error',
    },
  },
  
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      '.vscode/**',
      'public/**',
      '*.config.js',
    ],
  },
]
