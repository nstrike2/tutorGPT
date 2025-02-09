// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.[jt]sx?$': 'babel-jest' // Transform your JS and JSX files using babel-jest
  },
  transformIgnorePatterns: [
    // Transform all modules except these so that axios (and others) are processed by babel-jest
    '/node_modules/(?!axios|react-markdown|remark-math|rehype-katex)'
  ],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy' // Handle CSS imports
  },
  extensionsToTreatAsEsm: ['.js', '.jsx']
}
