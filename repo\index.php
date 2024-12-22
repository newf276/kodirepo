
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<head>
<meta name="robots" content="noindex,nofollow">
</head>
<html>
  <body>
 <h1>Index of <? echo basename(__DIR__) ?></h1>
<hr>

<table>
  <thead>
        <tr>
          <th>Filename</th>
          <th>Type</th>
          <th>Size <small>(bytes)</small></th>
          <th>Date Modified</th>
        </tr>
  </thead>
  <tbody>
  <?php
     //logging errors//
     error_reporting(E_ALL | E_STRICT);
     ini_set('display_errors', false);
     ini_set('log_errors', false);
     ini_set('error_log','error_log.txt');
     //

    function ConvertSize($bytes){
       if ($bytes >= 1073741824){$bytes = number_format($bytes / 1073741824, 2) . ' GB';
       }elseif ($bytes >= 1048576){$bytes = number_format($bytes / 1048576, 2) . ' MB';
       }elseif ($bytes >= 1024){$bytes = number_format($bytes / 1024, 2) . ' KB';
       }elseif ($bytes > 1){$bytes = $bytes . ' bytes';
       }elseif ($bytes == 1){$bytes = $bytes . ' byte';
       }else{$bytes = '0 bytes';
       }
       return $bytes;
       }
    // Opens directory
    $myDirectory=opendir(".");
    
    // Gets each entry
    while($entryName = readdir($myDirectory)) {
     $pathinfo = pathinfo($entryName);
     if ($pathinfo['extension'] != 'html')
      if ($pathinfo['extension'] != 'php')
       //if($entryName != 'add_another_file_to_skip.ext')
        $dirArray[] = $entryName;
}
    
    // Finds extensions of files
    function findexts ($filename) {
      $filename=strtolower($filename);
      $exts=substr($filename, strrpos($filename, '.')+1);
      return $exts;
    }
    
    // Closes directory
    closedir($myDirectory);
    
    // Counts elements in array
    $indexCount=count($dirArray);
    
    // Sorts files
    sort($dirArray);
    
    // Loops through the array of files
    for($index=0; $index < $indexCount; $index++) {
    
      // hides .   and  ..  
      $hide=".";

      if(substr("$dirArray[$index]", 0, 1) != $hide) {
      
      // Gets File Names
      $name=$dirArray[$index];
      $namehref=$dirArray[$index];
      
      // Gets Extensions 
      $extn=findexts($dirArray[$index]); 
      
      // Gets file size 
      $size=ConvertSize(filesize($dirArray[$index]));
      
      // Gets Date Modified Data
      $modtime=date("M j Y g:i A", filemtime($dirArray[$index]));
      
      // Adds better ext names
      switch ($extn){
        case "png": $extn="PNG Image"; break;
        case "jpg": $extn="JPEG Image"; break;
        case "svg": $extn="SVG Image"; break;
        case "gif": $extn="GIF Image"; break;
        case "ico": $extn="Windows Icon"; break;
        
        case "txt": $extn="Text File"; break;
        case "log": $extn="Log File"; break;
        case "js": $extn="Javascript"; break;
        case "css": $extn="Stylesheet"; break;
        case "pdf": $extn="PDF Document"; break;
        
        case "zip": $extn="ZIP Archive"; break;
        case "bak": $extn="Backup File"; break;
        
        default: $extn=strtoupper($extn)." File"; break;
      }
      
      // Separates directories
      if(is_dir($dirArray[$index])) {
        $extn="&lt;Directory&gt;"; 
        $size="&lt;Directory&gt;"; 
        $class="dir";
      } else {
        $class="file";
      }
      
      // Print 'em
      print("
      <tr>
        <td><a href=\"$namehref\">$name</a></td>
        <td>$extn</td>
        <td>$size</td>
        <td>$modtime</td>
      </tr>");
      }
    }
  ?>
  </tbody>
</table>
</pre><hr><address>Proudly Served by Yours Truly Web Server at this place Port 8080</address>
</body>
</html>
