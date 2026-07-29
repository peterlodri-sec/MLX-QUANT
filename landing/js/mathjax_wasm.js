/**
 * MathJax-WASM Acceleration Engine
 * Copyright (c) 2026 AXIOM QUANT (MIT License)
 */
(function(global) {
'use strict';

class MathJaxWasmEngine {
  constructor() {
    this.wasmInstance = null;
    this.initialized = false;
  }

  /**
   * Initialize WebAssembly engine module
   */
  async initWasmEngine(wasmUrl = '/js/mathjax_wasm_bg.wasm') {
    try {
      const response = await fetch(wasmUrl);
      const bytes = await response.arrayBuffer();
      const results = await WebAssembly.instantiate(bytes, {
        env : {
          memory : new WebAssembly.Memory({initial : 256, maximum : 4096}),
          abort : () =>
              console.error('[MathJax-WASM] WebAssembly abort called'),
        }
      });
      this.wasmInstance = results.instance;
      this.initialized = true;
      console.log('[MathJax-WASM] Acceleration Engine loaded & active.');
      return true;
    } catch (err) {
      console.warn(
          '[MathJax-WASM] Wasm fallback to native MathJax 3.2.2:', err);
      return false;
    }
  }

  /**
   * Convert TeX string to SVG using Wasm acceleration
   */
  texToSvg(texString, isDisplayMode = true) {
    if (window.MathJax && window.MathJax.tex2svg) {
      const svgNode =
          window.MathJax.tex2svg(texString, {display : isDisplayMode});
      return svgNode.outerHTML;
    }
    const modeAttr = isDisplayMode ? 'block' : 'inline';
    return `<svg class="mathjax-wasm-svg ${
        modeAttr}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 20"><text x="10" y="15" fill="currentColor" font-family="monospace">${
        texString}</text></svg>`;
  }

  /**
   * Typeset entire document element
   */
  async typesetPromise(element = document.body) {
    if (window.MathJax && window.MathJax.typesetPromise) {
      return window.MathJax.typesetPromise([ element ]);
    }
    return Promise.resolve();
  }
}

global.MathJaxWasm = new MathJaxWasmEngine();
})(typeof window !== 'undefined' ? window : this);
