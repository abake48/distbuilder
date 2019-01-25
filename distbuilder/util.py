# Standard Libraries
from six import PY2, PY3  # @UnusedImport
from sys import argv, stdout, stderr, exit, \
    executable as PYTHON_PATH
from os import system, remove as removeFile, \
    getcwd, chdir, \
    getenv, listdir, makedirs as makeDir, rename # @UnusedImport   
from os.path import exists, isfile as isFile, \
    dirname as dirPath, normpath, realpath, relpath, \
    join as joinPath, split as splitPath, splitext as splitExt, \
    expanduser, \
    basename, pathsep      # @UnusedImport
from shutil import rmtree as removeDir, move, make_archive, \
    copytree as copyDir, copyfile as copyFile   # @UnusedImport
import platform
from tempfile import gettempdir
from subprocess import Popen, list2cmdline, \
    PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW
import traceback
from distutils.sysconfig import get_python_lib
import inspect  # @UnusedImport
from builtins import isinstance

# -----------------------------------------------------------------------------   
__plat = platform.system()
IS_WINDOWS         = __plat == "Windows"
IS_LINUX           = __plat == "Linux"
IS_MACOS           = __plat == "Darwin"

PY_EXT             = ".py"
PY_DIR             = dirPath( PYTHON_PATH )
SITE_PACKAGES_PATH = get_python_lib()

THIS_DIR           = dirPath( realpath( argv[0] ) )

# Windows 
PY_SCRIPTS_DIR     = joinPath( PY_DIR, "Scripts" ) 

# *Nix
USER_BIN_DIR       = "/usr/bin"
USER_LOCAL_BIN_DIR = "/usr/local/bin"
OPT_LOCAL_BIN_DIR  = "/opt/local/bin"

# Shockingly platform independent 
# (though can vary by os language and configuration...)
DESKTOP_DIR_NAME   = "Desktop"
# Windows Desktop actual resolution key
__CSIDL_DESKTOP_DIRECTORY = 16

# strictly Apple
_MACOS_APP_EXT                     = ".app"
_LAUNCH_MACOS_APP_CMD             = "open"
__LAUNCH_MACOS_APP_NEW_SWITCH      = "-n"
__LAUNCH_MACOS_APP_BLOCK_SWITCH    = "-W"
__INTERNAL_MACOS_APP_BINARY_TMPLT  = "%s/Contents/MacOS/%s"

# icons types across the platforms
_WINDOWS_ICON_EXT = ".ico"
_MACOS_ICON_EXT   = ".icns" 
_LINUX_ICON_EXT   = ".png" 

__NOT_SUPPORTED_MSG = ( "Sorry this operation is not supported " +
                        "this for this platform!" )

# -----------------------------------------------------------------------------  
def run( binPath, args=[], 
         wrkDir=None, isElevated=False, isDebug=False ):
    # TODO: finish isElevated logic (for windows, in debug mode...)    
    binDir, fileName = splitPath( binPath )   
    if wrkDir is None : wrkDir = binDir
    isMacApp = _isMacApp( binPath )
    if isDebug :
        if isMacApp:                
            binPath = __INTERNAL_MACOS_APP_BINARY_TMPLT % (
                  normBinaryName( fileName, isGui=True )
                , normBinaryName( fileName, isGui=False )  
            )                
        cmdList = [binPath]
        if isinstance(args,list): cmdList.extend( args )
        elif args is not None: cmdList.append( args )    
        print( 'cd "%s"' % (wrkDir,) )
        print( list2cmdline(cmdList) )
        p = Popen( cmdList, cwd=wrkDir, shell=False, 
                   stdout=PIPE, stderr=STDOUT, bufsize=1 )
        while p.poll() is None:
            stdout.write( p.stdout.readline() if PY2 else 
                          p.stdout.readline().decode() )
            stdout.flush()
        stdout.write( "\nReturn code: %d\n" % (p.returncode,) )
        stdout.flush()    
    else :     
        if isMacApp:     
            newArgs = [ __LAUNCH_MACOS_APP_NEW_SWITCH
                      , __LAUNCH_MACOS_APP_BLOCK_SWITCH 
                      , fileName
            ]
            if isinstance( args, list ): newArgs.extend( args ) 
            args=newArgs
            binPath = fileName = _LAUNCH_MACOS_APP_CMD
        if isinstance(args,list): args = list2cmdline(args)
        elif args is None: args=""
        elevate = "" if not isElevated or IS_WINDOWS else "sudo"  
        pwdCmd = "" if IS_WINDOWS or isMacApp else "./"
        cmd = ('%s %s%s %s' % (elevate, pwdCmd, fileName, args)).strip()
        _system( cmd, wrkDir )
    
def runPy( pyPath, args=[], isElevated=False ):
    wrkDir, fileName = splitPath( pyPath )
    pyArgs = [fileName]
    if isinstance(args,list): pyArgs.extend( args )
    run( PYTHON_PATH, pyArgs, wrkDir, isElevated, isDebug=False )

def _system( cmd, wrkDir=None ):
    if wrkDir is not None:
        initWrkDir = getcwd()
        print( 'cd "%s"' % (wrkDir,) )
        chdir( wrkDir  )
    cmd = __scrubSystemCmd( cmd )        
    print( cmd )
    system( cmd ) 
    print('')
    if wrkDir is not None: chdir( initWrkDir )

def __scrubSystemCmd( cmd ):
    """
    os.system is more convenient than the newer subprocess functions
    when the intention is to act as very thin wrapper over the shell. 
    There is just one MAJOR problem with it: 
    If the first character in the command is a quote (to escape a long path
    to the binary you are executing), then the limited (undesirable) parsing 
    built into the function can all fall apart.  So, this scrub function
    solves that...  
    """    
    if not cmd.startswith('"'): return cmd
    cmdParts = cmd[1:].split('"')
    safeBinPath = _escapePath( cmdParts[0] )
    args = '"'.join(cmdParts[1:]) # (the leading space will remain)
    return "%s%s" % (safeBinPath, args) 

__BATCH_ESCAPE_PATH_TMPLT = 'for %A in ("{0}") do @echo %~sA'             
def _escapePath( path ):
    if IS_WINDOWS :     
        if " " not in path: return path       
        return __batchOneLinerOutput( __BATCH_ESCAPE_PATH_TMPLT.format(path) )
    else: return path.replace(" ", "\\ ") 

# simply assuming cmd is on the system path...
# the newline in the batch causes it to execute when piped in via stdin
__BATCH_RUN_AND_RETURN_CMD = ["cmd","/K"]  
__BATCH_ONE_LINER_TMPLT = "{0} 1>&2\n"  
__BATCH_ONE_LINER_STARTUPINFO = STARTUPINFO()
__BATCH_ONE_LINER_STARTUPINFO.dwFlags |= STARTF_USESHOWWINDOW 
def __batchOneLinerOutput( batch ):
    cmd = __BATCH_ONE_LINER_TMPLT.format( batch )
    p = Popen( __BATCH_RUN_AND_RETURN_CMD, shell=False, 
               startupinfo=__BATCH_ONE_LINER_STARTUPINFO,
               stdin=PIPE, stdout=PIPE, stderr=PIPE )    
    # pipe cmd to stdin, return stdout, minus a trailing newline
    return p.communicate( cmd )[1].rstrip()  
            
# -----------------------------------------------------------------------------  
def moveToDesktop( path ): return _moveToDir( path, _userDesktopDirPath() )

def moveToHomeDir( path ): return _moveToDir( path, _userHomeDirPath() )
    
def _moveToDir( srcPath, destDirPath ):        
    destPath = joinPath( destDirPath, 
                         basename( normpath(srcPath) ) )
    if isFile( destPath ): removeFile( destPath )
    elif isDir( destPath ): removeDir( destPath )
    move( srcPath, destDirPath )
    print( 'Moved "%s" to "%s"' % (srcPath, destPath) )
    return destPath

# -----------------------------------------------------------------------------
__IMPORT_TMPLT       = "import %s"
__FROM_IMPORT_TMPLT  = "from %s import %s"
__GET_MOD_PATH_TMPLT = "inspect.getfile( %s )"

def isImportableModule( moduleName ):
    try: __importByStr( moduleName )
    except : return False
    return True

def isImportableFromModule( moduleName, memberName ):
    try: __importByStr( moduleName, memberName )
    except : return False
    return True

def modulePath( moduleName ):
    try: 
        exec( __IMPORT_TMPLT % (moduleName,) ) # cannot use __importByStr as that is outside of the scope!
        return eval( __GET_MOD_PATH_TMPLT % (moduleName,) )
    except Exception as e: 
        printExc( e )
        return None

def modulePackagePath( moduleName ):
    modPath = modulePath( moduleName )
    return None if modPath is None else dirPath( modPath )
    
def sitePackagePath( packageName ):
    packagePath = joinPath( SITE_PACKAGES_PATH, packageName )
    return packagePath if exists( packagePath ) else None

def __importByStr( moduleName, memberName=None ):
    try: 
        if memberName is None : exec( __IMPORT_TMPLT % (moduleName,) )
        else: exec( __FROM_IMPORT_TMPLT % (moduleName, memberName) )
    except Exception as e: printExc( e )

# -----------------------------------------------------------------------------
def toZipFile( sourceDir, zipDest=None, removeScr=True ):
    if zipDest is None :        
        zipDest = sourceDir # make_archive add extension
    else:
        if isFile( zipDest ) : removeFile( zipDest )
        zipDest, _ = splitExt(zipDest)           
    filePath = make_archive( zipDest, 'zip', sourceDir )
    print( 'Created zip file: "%s"' % (filePath,) )    
    if removeScr :         
        removeDir( sourceDir )
        print( 'Removed directory: "%s"' % (sourceDir,) )        
    return filePath
 
# -----------------------------------------------------------------------------   
def normBinaryName( path, isPathPreserved=False, isGui=False ):    
    if not isPathPreserved : path = basename( path )
    base, ext = splitExt( path )
    if IS_MACOS and isGui :
        return "%s%s" % (base, _MACOS_APP_EXT)      
    if IS_WINDOWS: return base + (".exe" if ext=="" else ext)
    return base 
                        
def _normIconName( path, isPathPreserved=False ):    
    if not isPathPreserved : path = basename( path )
    base, _ = splitExt( path )
    if IS_WINDOWS: return "%s%s" % (base, _WINDOWS_ICON_EXT) 
    elif IS_MACOS: return "%s%s" % (base, _MACOS_ICON_EXT) 
    elif IS_LINUX: return "%s%s" % (base, _LINUX_ICON_EXT) 
    raise Exception( __NOT_SUPPORTED_MSG )
    return base 
                        
def _isMacApp( path ): return IS_MACOS and splitExt(path)[1]==".app"

# -----------------------------------------------------------------------------      
def isDir( path ): return exists(path) and not isFile(path)

# absolute path relative to the script directory NOT the working directory    
def absPath( relativePath ):    
    return normpath( joinPath( THIS_DIR, relativePath ) )

def tempDirPath(): return gettempdir()

# -----------------------------------------------------------------------------                          
def _pythonPath( relativePath ):    
    return normpath( joinPath( PY_DIR, relativePath ) )

def _pythonScriptsPath( relativePath ):    
    return normpath( joinPath( PY_SCRIPTS_DIR, relativePath ) )

def _usrBinPath( relativePath ):    
    return normpath( joinPath( USER_BIN_DIR, relativePath ) )

def _usrLocalBinPath( relativePath ):    
    return normpath( joinPath( USER_LOCAL_BIN_DIR, relativePath ) )

def _optLocalBinPath( relativePath ):    
    return normpath( joinPath( OPT_LOCAL_BIN_DIR, relativePath ) )

def _userHiddenLocalBinDirPath( relativePath ) :
    return normpath( joinPath( "%s/.local/bin" % (_userHomeDirPath(),), 
                               relativePath ) )

def _userHomeDirPath(): return expanduser('~') # works in Windows too!
            
def _userDesktopDirPath():
    if IS_WINDOWS : 
        return __getFolderPathByCSIDL( __CSIDL_DESKTOP_DIRECTORY )
    elif IS_LINUX or IS_MACOS :
        return normpath( joinPath( _userHomeDirPath(), DESKTOP_DIR_NAME ) )
    raise Exception( __NOT_SUPPORTED_MSG )        
            
def __getFolderPathByCSIDL( csidl ):
    import ctypes.wintypes    
    SHGFP_TYPE_CURRENT = 0   # Get current, not default value
    buf = ctypes.create_unicode_buffer( ctypes.wintypes.MAX_PATH )
    ctypes.windll.shell32.SHGetFolderPathW( 
        None, csidl, None, SHGFP_TYPE_CURRENT, buf )
    return buf.value 
            
# -----------------------------------------------------------------------------    
def _toSrcDestPair( pathPair, destDir=None ):
    ''' UGLY "Protected" function for internal library uses ONLY! '''
    
    # this is private implementation detail
    isPyInstallerArg = (destDir is None) 
    
    src = dest = None             
    if( isinstance(pathPair, str) or
        isinstance(pathPair, unicode) ):  # @UndefinedVariable
        # shortcut syntax - only provide the source,
        # (the destination is relative)
        src = pathPair
    elif isinstance(pathPair, dict) :
        # if a dictionary is provided, use the first k/v pair  
        try : src, dest = pathPair.iteritems().next() 
        except: pass
    else: 
        # a two element tuple (or list) is the expected format
        try : src = pathPair[0] 
        except: pass
        try : dest = pathPair[1] 
        except: pass
    if src is None: return None
    src = normpath( src )
    srcHead, srcTail = splitPath( src )
    if srcHead=="" : 
        srcHead = THIS_DIR
        src = joinPath( srcHead, srcTail )
    if isPyInstallerArg:
        if dest is None: dest = relpath( srcHead )  # relative to cwd                   
    else :
        if dest is None:
            dest = joinPath( relpath( srcHead ), srcTail )         
        dest = normpath( joinPath( destDir, dest ) )                             
    return (src, dest) 

# -----------------------------------------------------------------------------           
def printErr( msg, isFatal=False ):
    try: stderr.write( str(msg) + "\n" )
    except: 
        try: stderr.write( unicode(msg) + "\n" )  # @UndefinedVariable
        except: stderr.write( "ERROR on: %s\n" % 
                (traceback.format_stack(limit=1)) )
    stderr.flush()        
    if isFatal: exit(1)   

def printExc( e, isDetailed=False, isFatal=False ):
    if isDetailed :
        printErr( repr(e) )
        printErr( "Stack Trace:" )
        printErr( traceback.format_exc() )
    else : printErr( e )
    if isFatal: exit(1)
            
# -----------------------------------------------------------------------------           
