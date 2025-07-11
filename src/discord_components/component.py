import discord
from discord import ui
from typing import Optional, Union, List, Dict, Callable, Any, Coroutine, TypeVar, TYPE_CHECKING
import asyncio
import inspect

if TYPE_CHECKING:
    from discord import Interaction, Message

T = TypeVar('T')

__all__ = (
    'ActionRow',
    'Button',
    'SelectMenu',
    'TextInput',
    'Component',
    'ComponentMessage',
    'ComponentContext',
    'component_handler'
)

class Component:
    def __init__(self, *, custom_id: Optional[str] = None, disabled: bool = False):
        self.custom_id = custom_id
        self.disabled = disabled
    
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        raise NotImplementedError

class Button(Component):
    def __init__(
        self,
        *,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        label: Optional[str] = None,
        emoji: Optional[Union[str, discord.Emoji, discord.PartialEmoji]] = None,
        url: Optional[str] = None,
        custom_id: Optional[str] = None,
        disabled: bool = False,
        row: Optional[int] = None
    ):
        super().__init__(custom_id=custom_id, disabled=disabled)
        self.style = style
        self.label = label
        self.emoji = emoji
        self.url = url
        self.row = row
    
    def to_dict(self) -> Dict[str, Any]:
        if self.url is not None:
            if self.custom_id is not None:
                raise ValueError('Button with URL cannot have a custom_id')
            if self.style not in (discord.ButtonStyle.link, discord.ButtonStyle.url):
                raise ValueError('Button with URL must have style set to ButtonStyle.link')
        
        data = {
            'type': 2,
            'style': self.style.value,
            'disabled': self.disabled
        }
        
        if self.label is not None:
            data['label'] = self.label
        if self.emoji is not None:
            if isinstance(self.emoji, str):
                data['emoji'] = {'name': self.emoji}
            else:
                data['emoji'] = {'name': self.emoji.name, 'id': self.emoji.id, 'animated': getattr(self.emoji, 'animated', False)}
        if self.url is not None:
            data['url'] = self.url
        if self.custom_id is not None:
            data['custom_id'] = self.custom_id
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Button':
        style = discord.ButtonStyle(data['style'])
        label = data.get('label')
        emoji = data.get('emoji')
        url = data.get('url')
        custom_id = data.get('custom_id')
        disabled = data.get('disabled', False)
        
        if emoji:
            if 'id' in emoji:
                emoji = discord.PartialEmoji(
                    name=emoji['name'],
                    id=emoji['id'],
                    animated=emoji.get('animated', False)
                )
            else:
                emoji = emoji['name']
        
        return cls(
            style=style,
            label=label,
            emoji=emoji,
            url=url,
            custom_id=custom_id,
            disabled=disabled
        )

class SelectOption:
    def __init__(
        self,
        *,
        label: str,
        value: str,
        description: Optional[str] = None,
        emoji: Optional[Union[str, discord.Emoji, discord.PartialEmoji]] = None,
        default: bool = False
    ):
        self.label = label
        self.value = value
        self.description = description
        self.emoji = emoji
        self.default = default
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            'label': self.label,
            'value': self.value,
            'default': self.default
        }
        
        if self.description is not None:
            data['description'] = self.description
        if self.emoji is not None:
            if isinstance(self.emoji, str):
                data['emoji'] = {'name': self.emoji}
            else:
                data['emoji'] = {'name': self.emoji.name, 'id': self.emoji.id, 'animated': getattr(self.emoji, 'animated', False)}
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SelectOption':
        label = data['label']
        value = data['value']
        description = data.get('description')
        emoji = data.get('emoji')
        default = data.get('default', False)
        
        if emoji:
            if 'id' in emoji:
                emoji = discord.PartialEmoji(
                    name=emoji['name'],
                    id=emoji['id'],
                    animated=emoji.get('animated', False)
                )
            else:
                emoji = emoji['name']
        
        return cls(
            label=label,
            value=value,
            description=description,
            emoji=emoji,
            default=default
        )

class SelectMenu(Component):
    def __init__(
        self,
        *,
        custom_id: str,
        options: List[SelectOption],
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None
    ):
        super().__init__(custom_id=custom_id, disabled=disabled)
        self.options = options
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.row = row
    
    def to_dict(self) -> Dict[str, Any]:
        if len(self.options) > 25:
            raise ValueError('SelectMenu can only have up to 25 options')
        
        data = {
            'type': 3,
            'custom_id': self.custom_id,
            'options': [option.to_dict() for option in self.options],
            'min_values': self.min_values,
            'max_values': self.max_values,
            'disabled': self.disabled
        }
        
        if self.placeholder is not None:
            data['placeholder'] = self.placeholder
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SelectMenu':
        custom_id = data['custom_id']
        options = [SelectOption.from_dict(option) for option in data['options']]
        placeholder = data.get('placeholder')
        min_values = data.get('min_values', 1)
        max_values = data.get('max_values', 1)
        disabled = data.get('disabled', False)
        
        return cls(
            custom_id=custom_id,
            options=options,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled
        )

class TextInput(Component):
    def __init__(
        self,
        *,
        custom_id: str,
        label: str,
        style: discord.TextStyle = discord.TextStyle.short,
        placeholder: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        required: bool = True,
        default: Optional[str] = None,
        disabled: bool = False
    ):
        super().__init__(custom_id=custom_id, disabled=disabled)
        self.label = label
        self.style = style
        self.placeholder = placeholder
        self.min_length = min_length
        self.max_length = max_length
        self.required = required
        self.default = default
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            'type': 4,
            'custom_id': self.custom_id,
            'label': self.label,
            'style': self.style.value,
            'required': self.required,
            'disabled': self.disabled
        }
        
        if self.placeholder is not None:
            data['placeholder'] = self.placeholder
        if self.min_length is not None:
            data['min_length'] = self.min_length
        if self.max_length is not None:
            data['max_length'] = self.max_length
        if self.default is not None:
            data['value'] = self.default
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextInput':
        custom_id = data['custom_id']
        label = data['label']
        style = discord.TextStyle(data['style'])
        placeholder = data.get('placeholder')
        min_length = data.get('min_length')
        max_length = data.get('max_length')
        required = data.get('required', True)
        default = data.get('value')
        disabled = data.get('disabled', False)
        
        return cls(
            custom_id=custom_id,
            label=label,
            style=style,
            placeholder=placeholder,
            min_length=min_length,
            max_length=max_length,
            required=required,
            default=default,
            disabled=disabled
        )

class ActionRow:
    def __init__(self, *components: Component):
        self.components = list(components)
    
    def to_dict(self) -> Dict[str, Any]:
        if len(self.components) > 5:
            raise ValueError('ActionRow can only contain up to 5 components')
        
        return {
            'type': 1,
            'components': [component.to_dict() for component in self.components]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionRow':
        components = []
        
        for component_data in data['components']:
            component_type = component_data['type']
            
            if component_type == 2:  
                components.append(Button.from_dict(component_data))
            elif component_type == 3:  
                components.append(SelectMenu.from_dict(component_data))
            elif component_type == 4: 
                components.append(TextInput.from_dict(component_data))
            else:
                raise ValueError(f'Unknown component type: {component_type}')
        
        return cls(*components)

class ComponentMessage:
    def __init__(
        self,
        *,
        content: Optional[str] = None,
        embeds: Optional[List[discord.Embed]] = None,
        components: Optional[List[Union[ActionRow, List[Component]]]] = None,
        **kwargs
    ):
        self.content = content
        self.embeds = embeds or []
        self._components = []
        self._view = None
        self._message = None
        self._interaction = None
        self._timeout = kwargs.get('timeout', 180.0)
        self._listeners = {}
        
        if components:
            for component in components:
                if isinstance(component, ActionRow):
                    self._components.append(component)
                elif isinstance(component, list):
                    self._components.append(ActionRow(*component))
                else:
                    raise TypeError(f'Expected ActionRow or list of Components, got {type(component)}')
    
    @property
    def components(self) -> List[ActionRow]:
        return self._components
    
    @property
    def view(self) -> Optional[ui.View]:
        return self._view
    
    @property
    def message(self) -> Optional['Message']:
        return self._message
    
    @property
    def interaction(self) -> Optional['Interaction']:
        return self._interaction
    
    def to_dict(self) -> Dict[str, Any]:
        data = {}
        
        if self.content is not None:
            data['content'] = self.content
        if self.embeds:
            data['embeds'] = [embed.to_dict() for embed in self.embeds]
        if self._components:
            data['components'] = [row.to_dict() for row in self._components]
        
        return data
    
    def add_component(self, component: Union[Component, ActionRow], row: Optional[int] = None):
        if isinstance(component, ActionRow):
            if len(self._components) >= 5:
                raise ValueError('Cannot have more than 5 action rows')
            self._components.append(component)
            return
        
        if row is not None:
            if row < 0 or row >= 5:
                raise ValueError('Row must be between 0 and 4')
            
            while len(self._components) <= row:
                self._components.append(ActionRow())
            
            if len(self._components[row].components) >= 5:
                raise ValueError('Cannot have more than 5 components in a row')
            
            self._components[row].components.append(component)
        else:
            if not self._components or len(self._components[-1].components) >= 5:
                if len(self._components) >= 5:
                    raise ValueError('Cannot have more than 5 action rows')
                self._components.append(ActionRow(component))
            else:
                self._components[-1].components.append(component)
    
    def remove_component(self, custom_id: str) -> bool:
        for row in self._components:
            for i, component in enumerate(row.components):
                if getattr(component, 'custom_id', None) == custom_id:
                    row.components.pop(i)
                    if not row.components:
                        self._components.remove(row)
                    return True
        return False
    
    def clear_components(self):
        self._components.clear()
    
    def to_view(self) -> ui.View:
        view = ui.View(timeout=self._timeout)
        
        for row_idx, row in enumerate(self._components):
            for component in row.components:
                if isinstance(component, Button):
                    button = ui.Button(
                        style=component.style,
                        label=component.label,
                        emoji=component.emoji,
                        url=component.url,
                        custom_id=component.custom_id,
                        disabled=component.disabled,
                        row=row_idx
                    )
                    
                    if component.custom_id and component.custom_id in self._listeners:
                        button.callback = self._listeners[component.custom_id]
                    
                    view.add_item(button)
                
                elif isinstance(component, SelectMenu):
                    select = ui.Select(
                        custom_id=component.custom_id,
                        placeholder=component.placeholder,
                        min_values=component.min_values,
                        max_values=component.max_values,
                        disabled=component.disabled,
                        options=[
                            discord.SelectOption(
                                label=opt.label,
                                value=opt.value,
                                description=opt.description,
                                emoji=opt.emoji,
                                default=opt.default
                            ) for opt in component.options
                        ],
                        row=row_idx
                    )
                    
                    if component.custom_id in self._listeners:
                        select.callback = self._listeners[component.custom_id]
                    
                    view.add_item(select)
        
        self._view = view
        return view
    
    def on_interaction(self, custom_id: str) -> Callable[[T], T]:
        def decorator(coro: T) -> T:
            if not inspect.iscoroutinefunction(coro):
                raise TypeError('Callback must be a coroutine function')
            
            self._listeners[custom_id] = coro
            return coro
        return decorator
    
    async def send(self, ctx: Union['discord.Interaction', 'discord.ext.commands.Context'], **kwargs) -> 'Message':
        if isinstance(ctx, discord.Interaction):
            if ctx.response.is_done():
                send_func = ctx.followup.send
            else:
                send_func = ctx.response.send_message
        else:
            send_func = ctx.send
        
        if 'view' not in kwargs:
            kwargs['view'] = self.to_view()
        
        message = await send_func(
            content=self.content,
            embeds=self.embeds,
            **kwargs
        )
        
        self._message = message
        if isinstance(ctx, discord.Interaction):
            self._interaction = ctx
        
        return message
    
    async def edit(self, **kwargs) -> Optional['Message']:
        if not self._message and not self._interaction:
            raise ValueError('No message or interaction to edit')
        
        if 'view' not in kwargs:
            kwargs['view'] = self.to_view()
        
        if self._message:
            await self._message.edit(
                content=self.content,
                embeds=self.embeds,
                **kwargs
            )
            return self._message
        elif self._interaction:
            if self._interaction.response.is_done():
                await self._interaction.edit_original_response(
                    content=self.content,
                    embeds=self.embeds,
                    **kwargs
                )
            else:
                await self._interaction.response.edit_message(
                    content=self.content,
                    embeds=self.embeds,
                    **kwargs
                )
            return await self._interaction.original_response()

class ComponentContext:
    def __init__(self, interaction: discord.Interaction, component: Component):
        self.interaction = interaction
        self.component = component
        self.bot = interaction.client
        self.guild = interaction.guild
        self.channel = interaction.channel
        self.user = interaction.user
        self.message = interaction.message
        self.custom_id = getattr(component, 'custom_id', None)
        self.values = getattr(component, 'values', [])
    
    async def defer(self, *, ephemeral: bool = False) -> None:
        await self.interaction.response.defer(ephemeral=ephemeral)
    
    async def reply(self, content: Optional[str] = None, **kwargs) -> None:
        await self.interaction.response.send_message(content, **kwargs)
    
    async def edit(self, content: Optional[str] = None, **kwargs) -> None:
        if self.interaction.response.is_done():
            await self.interaction.edit_original_response(content=content, **kwargs)
        else:
            await self.interaction.response.edit_message(content=content, **kwargs)
    
    async def update(self, **kwargs) -> None:
        if 'content' not in kwargs and 'embeds' not in kwargs and 'view' not in kwargs:
            kwargs['content'] = None
        
        await self.interaction.response.edit_message(**kwargs)

def component_handler(bot):
    def decorator(func):
        @bot.listen('on_interaction')
        async def on_interaction(interaction: discord.Interaction):
            if not interaction.type == discord.InteractionType.component:
                return
            
            custom_id = None
            component = None
            
            if interaction.data.get('component_type') == 2:  
                custom_id = interaction.data['custom_id']
                component = Button.from_dict({
                    'type': 2,
                    'style': interaction.data.get('style', 2),
                    'label': interaction.data.get('label'),
                    'emoji': interaction.data.get('emoji'),
                    'custom_id': custom_id,
                    'disabled': False
                })
            elif interaction.data.get('component_type') == 3:  
                custom_id = interaction.data['custom_id']
                component = SelectMenu.from_dict({
                    'type': 3,
                    'custom_id': custom_id,
                    'options': [],
                    'values': interaction.data.get('values', []),
                    'min_values': interaction.data.get('min_values', 1),
                    'max_values': interaction.data.get('max_values', 1),
                    'disabled': False
                })
            
            if component:
                ctx = ComponentContext(interaction, component)
                await func(ctx)
        
        return func
    return decorator
