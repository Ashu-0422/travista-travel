import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

// Use --dart-define=APP_URL=https://your-domain.com to set your production URL.
const String appUrl = String.fromEnvironment(
  'APP_URL',
  defaultValue: 'https://your-domain.com',
);

void main() {
  runApp(const TravistaApp());
}

class TravistaApp extends StatelessWidget {
  const TravistaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Travista',
      home: TravistaWebView(url: appUrl),
    );
  }
}

class TravistaWebView extends StatefulWidget {
  const TravistaWebView({super.key, required this.url});

  final String url;

  @override
  State<TravistaWebView> createState() => _TravistaWebViewState();
}

class _TravistaWebViewState extends State<TravistaWebView> {
  late final WebViewController _controller;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) => setState(() => _isLoading = true),
          onPageFinished: (_) => setState(() => _isLoading = false),
        ),
      )
      ..loadRequest(Uri.parse(widget.url));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Stack(
          children: [
            WebViewWidget(controller: _controller),
            if (_isLoading)
              const Center(
                child: CircularProgressIndicator(),
              ),
          ],
        ),
      ),
    );
  }
}
