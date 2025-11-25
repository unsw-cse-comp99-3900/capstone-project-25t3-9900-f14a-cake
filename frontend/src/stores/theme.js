/**
 * Theme store for managing application theme (light/dark mode).
 * 
 * @module stores/theme
 */

import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

/**
 * Theme store using Pinia.
 * 
 * Manages application theme state and provides methods to toggle between
 * light and dark themes. The theme preference is persisted in localStorage.
 * 
 * @returns {Object} Store object with theme state and methods
 * @property {import('vue').Ref<string>} theme - Current theme ('light' or 'dark')
 * @property {Function} toggleTheme - Toggle between light and dark theme
 * @property {Function} setTheme - Set specific theme
 */
export const useThemeStore = defineStore('theme', () => {
  // Get initial theme from localStorage or default to 'dark'
  const theme = ref(localStorage.getItem('theme') || 'dark')

  /**
   * Apply theme to document.
   * 
   * Sets the data-theme attribute on the document element and saves
   * the theme preference to localStorage.
   * 
   * @param {string} newTheme - Theme name ('light' or 'dark')
   */
  const applyTheme = (newTheme) => {
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('theme', newTheme)
  }

  /**
   * Toggle between light and dark theme.
   * 
   * Switches the current theme to the opposite value and applies it.
   */
  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    applyTheme(theme.value)
  }

  /**
   * Set specific theme.
   * 
   * Sets the theme to the specified value if it's a valid theme name.
   * 
   * @param {string} newTheme - Theme name ('light' or 'dark')
   */
  const setTheme = (newTheme) => {
    if (newTheme === 'light' || newTheme === 'dark') {
      theme.value = newTheme
      applyTheme(newTheme)
    }
  }

  // Initialize theme on store creation
  applyTheme(theme.value)

  // Watch for theme changes
  watch(theme, (newTheme) => {
    applyTheme(newTheme)
  })

  return {
    theme,
    toggleTheme,
    setTheme
  }
})

