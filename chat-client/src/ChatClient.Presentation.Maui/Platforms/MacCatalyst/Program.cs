using ObjCRuntime;
using UIKit;

namespace ChatClient.Presentation.Maui;

public class Program
{
    /// <summary>
    /// The main entry point for the MacCatalyst application.
    /// </summary>
    /// <param name="args">Command line arguments.</param>
    static void Main(string[] args)
    {
        UIApplication.Main(args, null, typeof(AppDelegate));
    }
}
