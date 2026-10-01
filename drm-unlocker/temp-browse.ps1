Add-Type -AssemblyName System.Windows.Forms
$ofd = New-Object System.Windows.Forms.OpenFileDialog
$ofd.Filter = 'PowerPoint|*.pptx;*.ppt|All|*.*'
$ofd.InitialDirectory = [Environment]::GetFolderPath("Desktop")
if ($ofd.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $ofd.FileName }