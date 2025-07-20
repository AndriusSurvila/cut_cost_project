const components = import.meta.glob('./**/*.vue', { eager: true })

const exportedComponents = {}

for (const path in components) {
  const componentName = path.split('/').pop().replace('.vue', '')
  exportedComponents[componentName] = components[path].default
}

export default exportedComponents
