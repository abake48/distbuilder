from distbuilder import SimplePyToBinInstallerProcess, ConfigFactory

f = configFactory  = ConfigFactory()
f.productName      = "Hello World Example"
f.description      = "A Distribution Builder Example"
f.companyTradeName = "Some Company"
f.companyLegalName = "Some Company Inc."    
f.binaryName       = "HelloWorld"
f.isGui            = True        
f.entryPointPy     = "hello.py"  
f.iconFilePath     = "demo.ico" 
f.version          = (1,0,0,0)
f.setupName        = "HelloWorldSetup.exe"

class BuildProcess( SimplePyToBinInstallerProcess ):
    def onOpyConfig( self, cfg ):    
        cfg.external_modules.extend( [ 'tkinter', 'tkinter.ttk' ] )
p = BuildProcess( configFactory, isObfuscating=True, isDesktopTarget=True )
p.isTestingInstall = True
p.run()       