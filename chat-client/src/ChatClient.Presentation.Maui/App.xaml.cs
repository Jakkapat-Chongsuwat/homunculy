namespace ChatClient.Presentation.Maui;

/// <summary>
/// MAUI application class.
/// </summary>
public partial class App : Microsoft.Maui.Controls.Application
{
    public App()
    {
        InitializeComponent();
    }

    protected override Window CreateWindow(IActivationState? activationState)
    {
        return new Window(new MainPage());
    }
}
