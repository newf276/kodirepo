
# Popcorn (plugin.video.popcorn)

Popcorn is a multi-source addon for Kodi with the added ability to install custom provider modules. Unlike other Kodi addons which are generally built for a single service use, Popcorn allows users to connect to multiple online/offline services at once for their viewing with a single click.

## Contribution

Install all dependencies in requirements.txt
```shell
pip install -r requirements.txt
```

Configure hooks for automated pre commit changes:
```sh
pre-commit install
```
Ensure that `git` is available in your PATH

## FAQ

> #### How do I install a new provider?

In the settings menu of Popcorn you will find a providers tab. Inside this tab you will find the install provider package option.

> #### How do manage my providers?

Within Popcorn's settings, you will find the providers tab. Within this tab you can disable/enable single providers inside provide packs, enable/disable entire provider packages, enable/ disable automatic provider updates and manually for a update check for your providers.

> #### Popcorn won't show me season or episode lists and instead begins playing automatically?

Please disable the Auto Episode Resume setting in the general tab of Popcorn's settings.

> #### I'm experiencing an issue whilst using Popcorn. Where can I get help?
You can often find help from users in the Addons4Kodi subreddit or you are always welcome to log a github issue and I will contact you directly to investigate the issue.

## License

Licensed under The GPL License.
