import json from 'rollup-plugin-json';
import babel from 'rollup-plugin-babel';
import multiEntry from 'rollup-plugin-multi-entry';
import includePaths from 'rollup-plugin-includepaths';


var route = "daviscoursesearch/flaskapp/static/js/";

var includePathOptions = {
    include: {},
    paths: ['daviscoursesearch/flaskapp/static/js/modules', 'daviscoursesearch/flaskapp/templates/pages/answer.html'],
    external: [],
    extensions: ['.js']
};

export default {
  entry: route + 'main.js',
  moduleName: 'discourse',
  plugins: [ json(), babel({
    babelrc: false,
    presets: ['react', 'es2015-rollup', "stage-0"],
    exclude: 'node_modules/**',
  }, "transform-object-rest-spread"), includePaths(includePathOptions)],
  dest: route + 'compiled.js'
};