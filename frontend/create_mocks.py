import os
import json

base_dir = r"C:\Ai voice agent\frontend\node_modules"

mocks = {
    "zustand": {
        "package.json": {
            "name": "zustand",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
const React = require('react');
const create = (initializer) => {
  if (initializer === undefined) {
    return (init) => create(init);
  }
  let state;
  const listeners = new Set();
  const getState = () => state;
  const setState = (partial, replace) => {
    const nextState = typeof partial === 'function' ? partial(state) : partial;
    if (!Object.is(nextState, state)) {
      const previousState = state;
      state = (replace ?? (typeof nextState !== 'object' || nextState === null))
        ? nextState
        : Object.assign({}, state, nextState);
      listeners.forEach((listener) => listener(state, previousState));
    }
  };
  const subscribe = (listener) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };
  const api = { getState, setState, subscribe };
  state = initializer(setState, getState, api);
  const useStore = (selector) => {
    const [slice, setSlice] = React.useState(() => selector ? selector(state) : state);
    React.useEffect(() => {
      return subscribe((nextState) => {
        setSlice(selector ? selector(nextState) : nextState);
      });
    }, [selector]);
    return slice;
  };
  Object.assign(useStore, api);
  return useStore;
};
const persist = (config, options) => {
  return (set, get, api) => {
    const name = options?.name;
    const storage = options?.storage || {
      getItem: (key) => typeof window !== 'undefined' ? localStorage.getItem(key) : null,
      setItem: (key, val) => typeof window !== 'undefined' ? localStorage.setItem(key, val) : null,
    };
    const originalSet = set;
    const persistedSet = (partial, replace) => {
      originalSet(partial, replace);
      if (name) {
        storage.setItem(name, JSON.stringify({ state: get() }));
      }
    };
    let initialState = {};
    if (name) {
      try {
        const stored = storage.getItem(name);
        if (stored) {
          initialState = JSON.parse(stored).state || {};
        }
      } catch (e) {}
    }
    const state = config(persistedSet, get, api);
    return { ...state, ...initialState };
  };
};
module.exports = { create, persist };
module.exports.create = create;
module.exports.persist = persist;
module.exports.default = create;
""",
        "middleware.js": """
const { persist } = require('./index.js');
module.exports = { persist };
""",
        "index.d.ts": """
export declare function create<T>(initializer?: any): any;
export declare function persist<T>(config: any, options: any): any;
export default create;
""",
        "middleware.d.ts": """
export declare function persist<T>(config: any, options: any): any;
"""
    },
    "framer-motion": {
        "package.json": {
            "name": "framer-motion",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
const React = require('react');
const motion = new Proxy({}, {
  get(target, key) {
    if (typeof key === 'string') {
      const Component = React.forwardRef(({ children, ...props }, ref) => {
        const cleanedProps = {};
        const motionProps = [
          'initial', 'animate', 'exit', 'transition', 'variants', 
          'whileHover', 'whileTap', 'whileFocus', 'whileDrag', 'whileInView',
          'viewport', 'layout', 'layoutId', 'onLayoutAnimationComplete',
          'onAnimationStart', 'onAnimationComplete', 'onUpdate',
          'drag', 'dragConstraints', 'dragElastic', 'dragMomentum', 
          'dragTransition', 'dragPropagation', 'dragControls', 'dragListener'
        ];
        for (const p in props) {
          if (!motionProps.includes(p)) {
            cleanedProps[p] = props[p];
          }
        }
        return React.createElement(key, { ...cleanedProps, ref }, children);
      });
      Component.displayName = `motion.${key}`;
      return Component;
    }
  }
});
const AnimatePresence = ({ children }) => children;
module.exports = { motion, AnimatePresence };
""",
        "index.d.ts": """
export declare const motion: any;
export declare const AnimatePresence: any;
"""
    },
    "axios": {
        "package.json": {
            "name": "axios",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
const axios = {
  create(config) {
    const reqInterceptors = [];
    const resInterceptors = [];
    const instance = {
      defaults: { headers: {} },
      interceptors: {
        request: { use: (fn) => reqInterceptors.push(fn) },
        response: { use: (fn, errFn) => resInterceptors.push({ fn, errFn }) }
      },
      async request(cfg) {
        let finalCfg = { ...config, ...cfg };
        for (const interceptor of reqInterceptors) {
          finalCfg = await interceptor(finalCfg);
        }
        try {
          const urlStr = finalCfg.url || "";
          const fullUrl = urlStr.startsWith("http") ? urlStr : (finalCfg.baseURL || "") + urlStr;
          
          // Construct request body if post/put/patch
          let body = undefined;
          if (finalCfg.data) {
            if (finalCfg.data instanceof FormData) {
              body = finalCfg.data;
              // Remove Content-Type header to let browser set it with boundary
              if (finalCfg.headers) {
                delete finalCfg.headers["Content-Type"];
              }
            } else {
              body = JSON.stringify(finalCfg.data);
            }
          }
          
          const res = await fetch(fullUrl, {
            method: finalCfg.method || 'GET',
            headers: finalCfg.headers || {},
            body
          });
          
          let responseData = {};
          try {
            responseData = await res.json();
          } catch(e) {}
          
          let response = { data: responseData, status: res.status, headers: res.headers };
          for (const interceptor of resInterceptors) {
            if (interceptor.fn) response = await interceptor.fn(response);
          }
          return response;
        } catch (err) {
          let error = err;
          for (const interceptor of resInterceptors) {
            if (interceptor.errFn) {
              try {
                error = await interceptor.errFn(error);
              } catch (newErr) {
                error = newErr;
              }
            }
          }
          throw error;
        }
      },
      get(url, cfg) { return this.request({ method: 'GET', url, ...cfg }); },
      post(url, data, cfg) { return this.request({ method: 'POST', url, data, ...cfg }); },
      put(url, data, cfg) { return this.request({ method: 'PUT', url, data, ...cfg }); },
      patch(url, data, cfg) { return this.request({ method: 'PATCH', url, data, ...cfg }); },
      delete(url, cfg) { return this.request({ method: 'DELETE', url, ...cfg }); }
    };
    return instance;
  }
};
module.exports = axios;
module.exports.default = axios;
""",
        "index.d.ts": """
declare const axios: any;
export default axios;
"""
    },
    "swr": {
        "package.json": {
            "name": "swr",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
const React = require('react');
function useSWR(key, fetcher, options) {
  const [data, setData] = React.useState(undefined);
  const [error, setError] = React.useState(undefined);
  const [isValidating, setIsValidating] = React.useState(false);
  React.useEffect(() => {
    if (!key) return;
    setIsValidating(true);
    const run = async () => {
      try {
        const res = fetcher ? await fetcher(key) : await fetch(key).then(r => r.json());
        setData(res);
      } catch (err) {
        setError(err);
      } finally {
        setIsValidating(false);
      }
    };
    run();
  }, [key]);
  return { data, error, isValidating, mutate: () => {} };
}
module.exports = useSWR;
module.exports.default = useSWR;
""",
        "index.d.ts": """
declare const useSWR: any;
export default useSWR;
"""
    },
    "clsx": {
        "package.json": {
            "name": "clsx",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
function clsx(...inputs) {
  const classes = [];
  for (const input of inputs) {
    if (!input) continue;
    if (typeof input === 'string' || typeof input === 'number') {
      classes.push(input);
    } else if (Array.isArray(input)) {
      classes.push(clsx(...input));
    } else if (typeof input === 'object') {
      for (const key in input) {
        if (input[key]) {
          classes.push(key);
        }
      }
    }
  }
  return classes.join(' ');
}
module.exports = clsx;
module.exports.default = clsx;
""",
        "index.d.ts": """
declare function clsx(...inputs: any[]): string;
export default clsx;
"""
    },
    "tailwind-merge": {
        "package.json": {
            "name": "tailwind-merge",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
function twMerge(...inputs) {
  return inputs.filter(Boolean).join(' ');
}
module.exports = { twMerge };
""",
        "index.d.ts": """
export declare function twMerge(...inputs: any[]): string;
"""
    },
    "class-variance-authority": {
        "package.json": {
            "name": "class-variance-authority",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
function cva(base, options) {
  return (props) => {
    const { variants, defaultVariants } = options || {};
    let classes = [base];
    for (const key in variants) {
      const selected = props?.[key] !== undefined ? props[key] : defaultVariants?.[key];
      if (selected !== undefined && variants[key][selected]) {
        classes.push(variants[key][selected]);
      }
    }
    if (props?.className) {
      classes.push(props.className);
    }
    return classes.filter(Boolean).join(' ');
  };
}
module.exports = { cva };
""",
        "index.d.ts": """
export declare function cva(base: any, options?: any): any;
"""
    },
    "react-hot-toast": {
        "package.json": {
            "name": "react-hot-toast",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
const React = require('react');
const toast = (msg) => console.log('toast:', msg);
toast.success = (msg) => console.log('toast success:', msg);
toast.error = (msg) => console.error('toast error:', msg);
toast.loading = (msg) => console.log('toast loading:', msg);
toast.dismiss = () => {};
const Toaster = () => null;
module.exports = toast;
module.exports.toast = toast;
module.exports.default = toast;
module.exports.Toaster = Toaster;
""",
        "index.d.ts": """
declare const toast: any;
export declare const Toaster: any;
export default toast;
"""
    },
    "react-markdown": {
        "package.json": {
            "name": "react-markdown",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
const React = require('react');
function ReactMarkdown({ children, components, remarkPlugins }) {
  return React.createElement('div', { className: 'prose prose-invert' }, children);
}
module.exports = ReactMarkdown;
module.exports.default = ReactMarkdown;
""",
        "index.d.ts": """
declare const ReactMarkdown: any;
export default ReactMarkdown;
"""
    },
    "remark-gfm": {
        "package.json": {
            "name": "remark-gfm",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
module.exports = () => {};
""",
        "index.d.ts": """
declare const remarkGfm: any;
export default remarkGfm;
"""
    },
    "react-syntax-highlighter": {
        "package.json": {
            "name": "react-syntax-highlighter",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
const React = require('react');
function Prism({ children, language, style }) {
  return React.createElement('pre', null, React.createElement('code', { className: language }, children));
}
module.exports = { Prism };
""",
        "index.d.ts": """
export declare const Prism: any;
"""
    },
    "uuid": {
        "package.json": {
            "name": "uuid",
            "main": "./index.js",
            "types": "./index.d.ts"
        },
        "index.js": """
const v4 = () => Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
module.exports = { v4 };
""",
        "index.d.ts": """
export declare function v4(): string;
"""
    }
}

for name, files in mocks.items():
    pkg_dir = os.path.join(base_dir, name)
    os.makedirs(pkg_dir, exist_ok=True)
    for filename, content in files.items():
        file_path = os.path.join(pkg_dir, filename)
        if isinstance(content, dict):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content.strip() + "\n")

# Extra: react-syntax-highlighter dist/esm/styles/prism
extra_dir = os.path.join(base_dir, "react-syntax-highlighter", "dist", "esm", "styles")
os.makedirs(extra_dir, exist_ok=True)
with open(os.path.join(extra_dir, "prism.js"), "w", encoding='utf-8') as f:
    f.write("module.exports = { oneDark: {} };\n")

print("All mocks created successfully!")
