const fs = require('fs');
const path = require('path');

// Define the dependencies and the files to by copied
const dependencies = {
  jquery: [
    'dist/jquery.min.js',
  ],
  muicss: [
    'dist/css/mui.min.css',
    'dist/js/mui.min.js',
  ],
};

const nodeModulesDir = path.resolve(__dirname, '../node_modules');
const targetDir = path.resolve(__dirname, '../dashboard/static/lib');


// Copy the necessary files from node_modules to the target directory
for (const [pkg, files] of Object.entries(dependencies)) {

//  // Ensure the static lib directory exists
//  const pkgDestPath = path.join(targetDir, pkg);
//  if (!fs.existsSync(pkgDestPath)) {
//    fs.mkdirSync(pkgDestPath, { recursive: true });
//  }

  files.forEach((file) => {
    const srcPath = path.join(nodeModulesDir, pkg, file);
    const destPath = path.join(targetDir, pkg, file);
    const destDir = path.dirname(destPath);
    if (!fs.existsSync(destDir)) {
      fs.mkdirSync(destDir, { recursive: true });
    }

    if (fs.existsSync(srcPath)) {
      fs.copyFileSync(srcPath, destPath);
      console.log(`Copied ${srcPath} to ${destPath}`);
    } else {
      console.error(`File not found: ${srcPath}`);
    }
  });
}
