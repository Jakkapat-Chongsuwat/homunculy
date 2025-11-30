using System.Reactive.Linq;
using System.Reactive.Subjects;
using ChatClient.Domain.Abstractions;
using ChatClient.Domain.Entities;
using ChatClient.Domain.Events;
using ChatClient.Domain.ValueObjects;

namespace ChatClient.Application.ViewModels;

/// <summary>
/// Base ViewModel with reactive properties.
/// </summary>
public abstract class ViewModelBase : IDisposable
{
    private readonly CompositeDisposable _disposables = new();
    private bool _disposed;

    protected void AddDisposable(IDisposable disposable) =>
        _disposables.Add(disposable);

    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (_disposed) return;
        if (disposing) _disposables.Dispose();
        _disposed = true;
    }
}

/// <summary>
/// Simple composite disposable for managing subscriptions.
/// </summary>
internal sealed class CompositeDisposable : IDisposable
{
    private readonly List<IDisposable> _disposables = [];
    private bool _disposed;

    public void Add(IDisposable disposable)
    {
        if (_disposed) disposable.Dispose();
        else _disposables.Add(disposable);
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        foreach (var d in _disposables) d.Dispose();
        _disposables.Clear();
    }
}
