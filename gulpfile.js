/* global require */

var gulp = require('gulp');
var mainBowerFiles = require('gulp-main-bower-files');
var eslint = require('gulp-eslint');
var stylelint = require('gulp-stylelint');

var lintPathsJS = [
    'dashboard/static/js/*.js',
    'gulpfile.js'
];

var lintPathsCSS = [
    'dashboard/static/css/*.css'
];

gulp.task('js:lint', () => {
    return gulp.src(lintPathsJS)
        .pipe(eslint())
        .pipe(eslint.format())
        .pipe(eslint.failAfterError());
});

gulp.task('css:lint', () => {
    return gulp.src(lintPathsCSS)
        .pipe(stylelint({
            reporters: [{ formatter: 'string', console: true}]
        }));
});

gulp.task('bower', function(){
    return gulp.src('./bower.json')
        .pipe(mainBowerFiles())
        .pipe(gulp.dest('./dashboard/static/lib'));
});

gulp.task('default', function() {
    gulp.start('bower');
    gulp.start('js:lint');
    gulp.start('css:lint');
});
